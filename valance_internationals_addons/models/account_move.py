from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    vehicle_number = fields.Char(string="Vehicle Number")
