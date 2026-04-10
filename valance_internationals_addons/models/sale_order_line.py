from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    qty_on_hand = fields.Float(
        string="On Hand",
        related='product_id.qty_available'
    )


    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self.product_id and self.product_id.part_number and res.get('name'):
            # Replace first line with part_number-product_name
            parts = res['name'].split('\n', 1)
            parts[0] = f"{self.product_id.part_number}-{self.product_id.name}"
            res['name'] = '\n'.join(parts)
        return res
