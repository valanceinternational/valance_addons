from odoo import http
from odoo.http import request


class SaleOrderController(http.Controller):

    @http.route('/sale/orders', type='http', auth='user', website=True)
    def sale_orders_list(self, **kwargs):
        """Display list of confirmed sale orders for Valance company."""
        company = request.env['res.company'].sudo().search(
            [('name', 'ilike', 'valance')], limit=1,
        )
        domain = [('state', '=', 'sale')]
        if company:
            domain.append(('company_id', '=', company.id))
        orders = request.env['sale.order'].sudo().search(domain, order='date_order desc')
        return request.render('valance_internationals_addons.sale_orders_template', {
            'orders': orders,
        })

    @http.route('/sale/order/<int:order_id>', type='http', auth='user', website=True)
    def sale_order_detail(self, order_id, **kwargs):
        """Display detailed view of a specific sale order."""
        order = request.env['sale.order'].sudo().browse(order_id)
        return request.render('valance_internationals_addons.sale_order_detail_template', {
            'order': order,
        })

    @http.route('/sale/order/update', type='jsonrpc', auth='user')
    def update_order_line(self, order_line_id, price, **kwargs):
        """Update the price of an order line."""
        try:
            order_line = request.env['sale.order.line'].sudo().browse(order_line_id)
            order_line.sudo().write({'price_unit': price})
            return {
                'success': True,
                'message': 'Price updated successfully',
                'new_total': order_line.order_id.amount_total,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/sale/order/update_picking_date', type='jsonrpc', auth='user')
    def update_picking_date(self, order_id, picking_date, **kwargs):
        """Update the picking date of a sale order."""
        try:
            order = request.env['sale.order'].sudo().browse(order_id)
            order.write({'picking_date': picking_date or False})
            return {'success': True, 'message': 'Picking date updated'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/sale/order/update_qty', type='jsonrpc', auth='user')
    def update_order_line_qty(self, order_line_id, qty, **kwargs):
        """Update the quantity of an order line."""
        try:
            order_line = request.env['sale.order.line'].sudo().browse(order_line_id)
            qty = float(qty)
            if qty <= 0:
                return {'success': False, 'message': 'Quantity must be a positive number'}
            order_line.sudo().write({'product_uom_qty': qty})
            return {
                'success': True,
                'message': 'Quantity updated successfully',
                'new_total': order_line.order_id.amount_total,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/sale/order/create_invoice', type='jsonrpc', auth='user')
    def create_invoice(self, order_id, **kwargs):
        """Create a regular customer invoice from a sale order."""
        try:
            order = request.env['sale.order'].sudo().browse(order_id)
            if not order.exists():
                return {'success': False, 'message': 'Order not found'}
            if order.state != 'sale':
                return {'success': False, 'message': 'Order must be confirmed to create invoice'}
            invoices = order._create_invoices()
            return {
                'success': True,
                'message': 'Invoice created successfully',
                'invoice_ids': invoices.ids if invoices else [],
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
