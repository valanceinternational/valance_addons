from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lr_number = fields.Char(string="LR Number")
    part_number = fields.Char(string="Part Number")
    
    _part_number_uniq = models.Constraint(
        'unique(part_number)',
        'Part Number must be unique! A product with this Part Number already exists.',
    )
   
    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        compute='_compute_storage_location',
        store=True,
    )

    @api.depends('product_variant_ids.stock_quant_ids.location_id','product_variant_ids.stock_quant_ids.quantity')
    def _compute_storage_location(self):
        for product in self:
            quant = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0)
            ], limit=1, order='quantity desc')
            
            product.storage_location_id = quant.location_id if quant else False
