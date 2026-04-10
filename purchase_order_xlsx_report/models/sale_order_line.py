from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_on_hand = fields.Float(related="product_id.qty_available", string="Qty On Hand", readonly=True)
