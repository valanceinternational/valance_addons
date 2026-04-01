from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lr_number = fields.Char(string="LR Number")
    part_number = fields.Char(string="Part Number")
