import logging
import glob
import json
import os
from datetime import datetime
import pytz

from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied
from odoo.http import root

_logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

RESTRICTION_MSG = _(
    "Login not allowed during restricted hours. "
    "Please contact your administrator for access."
)


def _get_restriction_config(env):
    """Fetch the active restriction config record (singleton)."""
    return env['login.restriction.config'].sudo().search(
        [('active', '=', True)], limit=1
    )


def _is_restricted_hour_from_config(config):
    """Return True if current time falls inside the blocked window."""
    if not config:
        return False

    tz = pytz.timezone(config.timezone or 'Asia/Kolkata')
    now = datetime.now(tz=tz)
    now_minutes = now.hour * 60 + now.minute

    start_minutes = int(config.restrict_start_time * 60)
    end_minutes = int(config.restrict_end_time * 60)

    if start_minutes > end_minutes:
        return now_minutes >= start_minutes or now_minutes < end_minutes
    else:
        return start_minutes <= now_minutes < end_minutes


class LoginRestrictionConfig(models.Model):
    _name = 'login.restriction.config'
    _description = 'Login Time Restriction Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Config Name',
        required=True,
        default='Default Restriction',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    restrict_start_time = fields.Float(
        string='Restriction Start Time',
        required=True,
        default=20.0,
    )
    restrict_end_time = fields.Float(
        string='Restriction End Time',
        required=True,
        default=10.0,
    )
    restrict_group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Restricted User Group',
        required=True,
    )
    restriction_message = fields.Char(
        string='Restriction Message',
        default="Login not allowed during restricted hours. Please try again later.",
    )
    timezone = fields.Selection(
        selection='_tz_selections',
        string='Timezone',
        default='Asia/Kolkata',
        required=True,
    )
    start_time_display = fields.Char(
        string='Start',
        compute='_compute_time_display',
    )
    end_time_display = fields.Char(
        string='End',
        compute='_compute_time_display',
    )
    current_ist_time = fields.Char(
        string='Current Time (selected TZ)',
        compute='_compute_current_time',
    )
    is_restricted_now = fields.Boolean(
        string='Restriction Active Now?',
        compute='_compute_current_time',
    )

    @api.model
    def _tz_selections(self):
        return [(tz, tz) for tz in pytz.common_timezones]

    @api.depends('restrict_start_time', 'restrict_end_time')
    def _compute_time_display(self):
        for rec in self:
            rec.start_time_display = self._float_to_time_str(rec.restrict_start_time)
            rec.end_time_display = self._float_to_time_str(rec.restrict_end_time)

    @api.depends('restrict_start_time', 'restrict_end_time', 'timezone')
    def _compute_current_time(self):
        for rec in self:
            tz = pytz.timezone(rec.timezone or 'Asia/Kolkata')
            now = datetime.now(tz=tz)
            rec.current_ist_time = now.strftime('%Y-%m-%d %H:%M:%S %Z')
            rec.is_restricted_now = _is_restricted_hour_from_config(rec)

    @staticmethod
    def _float_to_time_str(value):
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return f'{hours:02d}:{minutes:02d}'

    @api.constrains('restrict_start_time', 'restrict_end_time')
    def _check_times(self):
        for rec in self:
            if not (0.0 <= rec.restrict_start_time < 24.0):
                raise ValueError("Start time must be between 0 and 23.99")
            if not (0.0 <= rec.restrict_end_time < 24.0):
                raise ValueError("End time must be between 0 and 23.99")
            if rec.restrict_start_time == rec.restrict_end_time:
                raise ValueError("Start and End times cannot be the same.")


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_menu_ids = fields.Many2many(
        comodel_name='ir.ui.menu',
        relation='res_users_allowed_menu_rel',
        string='Allowed Apps',
        domain=[('parent_id', '=', False)],
        help="Only these app menus will be visible to this user. "
             "Leave empty to show all apps.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['allowed_menu_ids']

    def write(self, vals):
        res = super().write(vals)
        if 'allowed_menu_ids' in vals:
            # Clear menu cache so visibility changes take effect immediately
            self.env.registry.clear_cache()
        return res

    def _login(self, credential, user_agent_env):
        auth_info = super()._login(credential, user_agent_env)
        uid = auth_info.get('uid')
        if not uid:
            return auth_info

        env = self.env
        config = _get_restriction_config(env)
        if config and _is_restricted_hour_from_config(config):
            user = env['res.users'].sudo().browse(uid)
            restricted_group = config.restrict_group_id
            if restricted_group and user in restricted_group.user_ids:
                login = credential.get('login', '')
                msg = config.restriction_message or RESTRICTION_MSG
                _logger.warning(
                    "Login blocked for '%s' (group: %s) — restricted hours.",
                    login, restricted_group.name,
                )
                raise AccessDenied(msg)

        return auth_info

    @api.model
    def force_logout_restricted_users(self):
        """Scheduled action: delete session files for restricted users."""
        config = _get_restriction_config(self.env)
        if not config or not _is_restricted_hour_from_config(config):
            return

        restricted_group = config.restrict_group_id
        if not restricted_group:
            return

        restricted_users = restricted_group.user_ids.filtered('active')
        if not restricted_users:
            return

        restricted_uids = set(restricted_users.ids)
        session_path = root.session_store.path
        count = 0

        for fname in glob.iglob(os.path.join(session_path, '*', '*')):
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                uid = data.get('uid') if isinstance(data, dict) else None
                if uid and uid in restricted_uids:
                    os.unlink(fname)
                    count += 1
            except Exception:
                continue

        if count:
            affected_logins = [u.login for u in restricted_users]
            _logger.info(
                "login_restriction cron: deleted %d session(s) for %s",
                count, affected_logins,
            )

    @api.model
    def get_login_restriction_info(self):
        config = _get_restriction_config(self.env)
        if not config:
            return {'is_restricted_now': False, 'config': False}

        tz = pytz.timezone(config.timezone or 'Asia/Kolkata')
        now = datetime.now(tz=tz)

        return {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'is_restricted_now': _is_restricted_hour_from_config(config),
            'start': LoginRestrictionConfig._float_to_time_str(config.restrict_start_time),
            'end': LoginRestrictionConfig._float_to_time_str(config.restrict_end_time),
            'message': config.restriction_message,
            'config': True,
        }
