{
    'name': 'Valance Internationals Addons',
    'description': 'Custom addons for Valance Internationals - sale order portal, warehouse notifications, and inventory extensions.',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'depends': ['product', 'stock', 'sale_management', 'purchase', 'website', 'portal', 'mail', 'account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/discuss_channel_data.xml',
        'views/sale_order_action.xml',
        'views/menu.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_portal_templates.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'valance_internationals_addons/static/src/css/sale_orders.css',
            'valance_internationals_addons/static/src/js/sale_orders.js',
        ],
        'web.assets_backend': [
            'valance_internationals_addons/static/src/js/copy_clipboard_text.js',
            'valance_internationals_addons/static/src/xml/copy_clipboard_text.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
