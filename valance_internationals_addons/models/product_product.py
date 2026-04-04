from odoo import models, fields, api
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search_display_name(self, operator, value):
        """Add part_number to the product search domain (used by product.template search)."""
        domain = super()._search_display_name(operator, value)
        if not value:
            return domain
        if operator in Domain.NEGATIVE_OPERATORS:
            return Domain.AND([domain, [('part_number', operator, value)]])
        else:
            return Domain.OR([domain, [('part_number', operator, value)]])

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Add part_number to product.product name_search (used when variant field is visible)."""
        res = super().name_search(name=name, domain=domain, operator=operator, limit=limit)
        if not name:
            return res
        found_ids = {r[0] for r in res}
        remaining = (limit - len(res)) if limit else None
        if remaining is None or remaining > 0:
            part_domain = (domain or []) + [
                ('part_number', operator, name),
                ('id', 'not in', list(found_ids)),
            ]
            part_products = self.search_fetch(part_domain, ['display_name'], limit=remaining)
            res += [(p.id, p.display_name) for p in part_products.sudo()]
        return res
