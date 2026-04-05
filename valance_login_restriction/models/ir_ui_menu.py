from odoo import models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug=debug)

        user = self.env.user
        allowed_menus = user.sudo().allowed_menu_ids
        if not allowed_menus:
            return visible

        allowed_root_ids = set(allowed_menus.ids)
        all_menus = self.sudo().search_fetch(
            [('id', 'in', list(visible))],
            ['parent_path'],
            order='id',
        )
        allowed_ids = set()
        for menu in all_menus:
            if not menu.parent_path:
                continue
            ancestors = [int(x) for x in menu.parent_path.strip('/').split('/') if x]
            if ancestors and ancestors[0] in allowed_root_ids:
                allowed_ids.add(menu.id)

        return frozenset(visible & allowed_ids)
