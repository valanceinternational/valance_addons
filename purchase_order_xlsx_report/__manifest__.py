{
    "name": "Purchase Order XLSX Report",
    "version": "19.0.1.0.0",
    "summary": "Print Purchase Order as Excel (XLSX), mirroring the standard PDF layout",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["purchase", "report_xlsx", "sale", "stock"],
    "data": [
        "report/purchase_order_xlsx.xml",
        "views/sale_order_views.xml",
        "views/product_template_views.xml"
    ],
    "installable": True,
}
