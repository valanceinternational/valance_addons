/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.SaleOrderDetail = publicWidget.Widget.extend({
    selector: '#order-detail-app',
    events: {
        'click #save-order-btn': '_onSaveOrder',
        'change .price-input': '_onPriceChange',
        'change .qty-input': '_onQtyChange',
    },

    /**
     * Initialize the widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this.orderId = this.$el.data('order-id');
        this.currencySymbol = this.$el.data('currency-symbol') || '$';
        this.currencyPosition = this.$el.data('currency-position') || 'before';
        this.changedLines = new Map();
        this.changedQtyLines = new Map();
        console.log('Sale Order Detail Widget Initialized for Order ID:', this.orderId);
    },

    /**
     * Format amount with currency symbol based on position
     */
    _formatCurrency: function (amount) {
        const formatted = amount.toFixed(2);
        if (this.currencyPosition === 'after') {
            return formatted + ' ' + this.currencySymbol;
        }
        return this.currencySymbol + ' ' + formatted;
    },

    /**
     * Handle qty input change
     */
    _onQtyChange: function (ev) {
        const $input = $(ev.currentTarget);
        const lineId = $input.data('line-id');
        const maxQty = parseInt($input.attr('placeholder'));
        let newQty = parseInt($input.val());

        // Enforce positive and not greater than original qty
        if (isNaN(newQty) || newQty < 1) {
            newQty = 1;
            $input.val(1);
        } else if (newQty > maxQty) {
            newQty = maxQty;
            $input.val(maxQty);
            this._showNotification(
                `Quantity cannot exceed the ordered quantity of ${maxQty}.`,
                'danger'
            );
        }
        this.changedQtyLines.set(lineId, newQty);
        $input.addClass('price-changed');
        this._updateTotal();
    },

    /**
     * Handle price input change
     */
    _onPriceChange: function (ev) {
        const $input = $(ev.currentTarget);
        const lineId = $input.data('line-id');
        let newPrice = parseFloat($input.val());

        // Enforce positive
        if (isNaN(newPrice) || newPrice < 0) {
            newPrice = 0;
            $input.val(0);
        }

        this.changedLines.set(lineId, newPrice);
        $input.addClass('price-changed');
        this._updateTotal();
    },

    /**
     * Update the total amount based on changed prices and quantities
     */
    _updateTotal: function () {
        let total = 0;
        const self = this;

        this.$('.line-item').each(function () {
            const $line = $(this);
            const $priceInput = $line.find('.price-input');
            const $qtyInput = $line.find('.qty-input');

            const price = parseFloat($priceInput.val()) || parseFloat($priceInput.attr('placeholder')) || 0;
            const qty = parseInt($qtyInput.val()) || parseInt($qtyInput.attr('placeholder')) || 0;

            total += price * qty;
        });

        $('#total-amount').text(self._formatCurrency(total));
    },

    /**
     * Handle save order button click
     */
    _onSaveOrder: async function (ev) {
        ev.preventDefault();

        const $btn = $(ev.currentTarget);
        const orderId = parseInt(this.el.dataset.orderId);

        // ---------- VALIDATION ----------
        let hasError = false;

        this.$('.price-input').each(function () {
            const val = $(this).val();
            if (!val || parseFloat(val) <= 0) {
                $(this).addClass('input-error');
                hasError = true;
            } else {
                $(this).removeClass('input-error');
            }
        });

        this.$('.qty-input').each(function () {
            const val = $(this).val();
            const maxQty = parseInt($(this).attr('placeholder'));
            const parsed = parseInt(val);
            if (!val || parsed < 1 || parsed > maxQty) {
                $(this).addClass('input-error');
                hasError = true;
            } else {
                $(this).removeClass('input-error');
            }
        });

        if (hasError) {
            this._showNotification(
                'Please enter valid positive values for all fields before saving.',
                'danger'
            );
            return;
        }

        // Disable button
        $btn.prop('disabled', true);
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Saving...');

        try {
            // ---------- SAVE PICKING DATE ----------
            const pickingDate = this.$('#picking-date').val();
            if (pickingDate) {
                await rpc('/sale/order/update_picking_date', {
                    order_id: orderId,
                    picking_date: pickingDate,
                });
            }

            // ---------- SAVE UPDATED QUANTITIES ----------
            if (this.changedQtyLines.size > 0) {
                for (const [lineId, qty] of this.changedQtyLines.entries()) {
                    await this._updateOrderLineQty(lineId, qty);
                }
                this.changedQtyLines.clear();
                this.$('.qty-input').removeClass('price-changed');
            }

            // ---------- SAVE UPDATED PRICES ----------
            if (this.changedLines.size > 0) {
                for (const [lineId, price] of this.changedLines.entries()) {
                    await this._updateOrderLine(lineId, price);
                }
                this.changedLines.clear();
                this.$('.price-input').removeClass('price-changed');
            }

            // ---------- CREATE INVOICE ----------
            const result = await rpc('/sale/order/create_invoice', {
                order_id: orderId,
            });

            if (result.success) {
                this._showNotification(
                    'Order saved and invoice created successfully!',
                    'success'
                );
            } else {
                this._showNotification(result.message, 'danger');
            }

        } catch (error) {
            console.error('Error:', error);
            this._showNotification(
                'Something went wrong while saving or creating the invoice.',
                'danger'
            );
        } finally {
            $btn.prop('disabled', false);
            $btn.html(`
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M16.7 7.8l-7.5 7.5-4.9-4.9"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"/>
                </svg> Save Order
            `);
        }
    },

    /**
     * Update a single order line price via JSON-RPC
     */
    _updateOrderLine: async function (lineId, price) {
        const result = await rpc('/sale/order/update', {
            order_line_id: lineId,
            price: price,
        });
        if (!result.success) {
            throw new Error(result.message || 'Price update failed');
        }
        return result;
    },

    /**
     * Update a single order line qty via JSON-RPC
     */
    _updateOrderLineQty: async function (lineId, qty) {
        const result = await rpc('/sale/order/update_qty', {
            order_line_id: lineId,
            qty: qty,
        });
        if (!result.success) {
            throw new Error(result.message || 'Quantity update failed');
        }
        return result;
    },

    /**
     * Show notification to user
     */
    _showNotification: function (message, type) {
        const $notification = $('<div>')
            .addClass(`alert alert-${type} sale-order-notification`)
            .css({
                position: 'fixed',
                top: '20px',
                right: '20px',
                zIndex: 9999,
                minWidth: '300px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                animation: 'slideInRight 0.3s ease-out'
            })
            .html(`
                <div class="d-flex align-items-center justify-content-between">
                    <span>${message}</span>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `);

        $('body').append($notification);

        setTimeout(() => {
            $notification.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    },
});

// Add CSS for visual feedback
const style = document.createElement('style');
style.textContent = `
    .price-input.price-changed,
    .qty-input.price-changed {
        border-color: #FFB020 !important;
        background-color: rgba(255, 176, 32, 0.05) !important;
    }
    .price-input.input-error,
    .qty-input.input-error {
        border-color: #dc3545 !important;
        background-color: rgba(220, 53, 69, 0.05) !important;
    }

    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

export default publicWidget.registry.SaleOrderDetail;
