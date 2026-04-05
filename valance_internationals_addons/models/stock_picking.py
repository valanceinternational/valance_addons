from odoo import models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    transfer_by = fields.Selection([
        ('transport', 'Transport'),
        ('by_hand', 'By Hand'),
    ], string="Transfer By")
    transfer_details = fields.Text(string="Details")
