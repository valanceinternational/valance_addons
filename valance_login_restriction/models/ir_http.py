import logging

from odoo import models
from odoo.http import request, SessionExpiredException

_logger = logging.getLogger(__name__)

_ALWAYS_ALLOWED_PREFIXES = (
    '/web/session/authenticate',
    '/web/session/destroy',
    '/web/login',
    '/web/logout',
    '/web/static',
    '/favicon',
    '/web/assets',
    '/web/session/logout',
    '/web/reset_password',
    '/web/signup',
)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls, endpoint):
        if request and request.session and request.session.uid:
            path = request.httprequest.path
            if not any(path.startswith(p) for p in _ALWAYS_ALLOWED_PREFIXES):
                try:
                    uid = request.session.uid
                    env = request.env
                    from .res_users import _get_restriction_config, _is_restricted_hour_from_config

                    config = _get_restriction_config(env)
                    if config and _is_restricted_hour_from_config(config):
                        restricted_group = config.restrict_group_id
                        if restricted_group:
                            user = env['res.users'].sudo().browse(uid)
                            if user in restricted_group.user_ids:
                                _logger.warning(
                                    "Force-logout: user '%s' (uid=%s) in group '%s' "
                                    "accessed '%s' during restricted hours.",
                                    user.login, uid, restricted_group.name, path,
                                )
                                request.session.logout(keep_db=True)
                                msg = (
                                    config.restriction_message
                                    or "Your session has been terminated. Login is not allowed during restricted hours."
                                )
                                raise SessionExpiredException(msg)
                except SessionExpiredException:
                    raise
                except Exception as exc:
                    _logger.exception(
                        "login_restriction: unexpected error in _dispatch: %s", exc
                    )

        return super()._dispatch(endpoint)
