from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lr_number = fields.Char(string="LR Number")
    part_number = fields.Char(string="Part Number")

    _part_number_uniq = models.Constraint(
        'unique(part_number)',
        'Part Number must be unique! A product with this Part Number already exists.',
    )
