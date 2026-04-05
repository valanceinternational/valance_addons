from odoo import models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id')
    def _compute_name(self):
        super()._compute_name()
        for line in self:
            if line.product_id and line.product_id.part_number and line.name:
                # Prepend part_number to the first line of the description
                parts = line.name.split('\n', 1)
                parts[0] = f"{line.product_id.part_number}-{line.product_id.name}"
                line.name = '\n'.join(parts)
