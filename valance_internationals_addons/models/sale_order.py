import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    picking_date = fields.Date(
        string="Picking Date",
        help="Scheduled date for warehouse picking",
    )

    order_lines_summary = fields.Text(
        string="Order Lines Summary",
        compute="_compute_order_lines_summary",
        store=False,
    )

    @api.depends('order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_unit', 'order_line.price_subtotal')
    def _compute_order_lines_summary(self):
        for order in self:
            lines = []
            for line in order.order_line.filtered(lambda l: l.product_id):
                qty = line.product_uom_qty
                amount_str = f"{line.price_total}"
                if qty > 1:
                    amount_str = f"{line.price_total} ({line.price_unit})"
                lines.append(
                    f"{line.product_id.name} | Qty: {qty} | "
                    f"Amount: {amount_str}"
                )
            order.order_lines_summary = "\n".join(lines)

    def action_mark_as_sent(self):
        """Mark quotation as sent without sending an email."""
        self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})

    def action_confirm(self):
        self._check_available_quantities()
        res = super().action_confirm()
        self._notify_warehouse_managers()
        return res

    def _notify_warehouse_managers(self):
        """Post to Warehouse Notifications channel when SO is confirmed."""
        channel = self.env.ref(
            'valance_internationals_addons.channel_warehouse_notifications',
            raise_if_not_found=False,
        )
        if not channel:
            return

        for order in self:
            body = self._build_channel_message(order)
            channel.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            _logger.info(
                "Warehouse notification posted for %s to channel '%s'",
                order.name, channel.name,
            )

    @staticmethod
    def _build_channel_message(order):
        """Build plain message for the Discuss channel."""
        customer = order.partner_id.display_name or "Unknown"
        confirmed_by = order.env.user.display_name

        products = []
        for line in order.order_line:
            if line.display_type:
                continue
            products.append(
                f"{line.product_id.display_name} x {line.product_uom_qty:.0f}"
            )

        msg = (
            f"Order {order.name} confirmed by {confirmed_by}.\n"
            f"Customer: {customer}\n"
            f"Products: {', '.join(products)}\n"
            f"Please prepare the packing."
        )
        return msg

    def _check_available_quantities(self):
        """Prevent confirmation if ordered quantity exceeds free stock."""
        error_lines = []

        for order in self:
            for line in order.order_line.filtered(
                lambda l: l.product_id and l.product_id.type == 'product'
            ):
                product = line.product_id
                ordered_qty = line.product_uom_qty
                available_qty = product.free_qty

                if ordered_qty > available_qty:
                    error_lines.append(
                        _(
                            "- %(product)s | Ordered: %(ordered)s | Available: %(available)s"
                        ) % {
                            'product': product.display_name,
                            'ordered': ordered_qty,
                            'available': available_qty,
                        }
                    )

        if error_lines:
            raise ValidationError(
                _(
                    "You cannot confirm this Sales Order due to insufficient stock:\n\n%s"
                ) % "\n".join(error_lines)
            )
