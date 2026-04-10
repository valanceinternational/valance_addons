from odoo import models


class PurchaseOrderXlsx(models.AbstractModel):
    _name = "report.purchase_order_xlsx_report.purchase_order_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Purchase Order XLSX Report"

    def generate_xlsx_report(self, workbook, data, orders):
        formats = self._build_formats(workbook)
        for order in orders:
            sheet_name = (order.name or "PO")[:31].replace("/", "_")
            sheet = workbook.add_worksheet(sheet_name)
            self._write_order(sheet, order, formats)

    def _build_formats(self, workbook):
        return {
            "th": workbook.add_format({
                "bold": True, "font_size": 10, "bg_color": "#875A7B",
                "font_color": "#FFFFFF", "border": 1, "align": "center", "valign": "vcenter",
            }),
            "td_text": workbook.add_format({
                "font_size": 9, "border": 1, "align": "left", "valign": "top", "text_wrap": True,
            }),
            "td_qty": workbook.add_format({
                "font_size": 9, "border": 1, "align": "right", "valign": "top",
                "num_format": "#,##0.00",
            }),
        }

    def _write_order(self, sheet, order, fmt):
        sheet.set_column("A:A", 30)
        sheet.set_column("B:B", 12)
        row = 0
        headers = ["Part Number", "Qty"]
        for col, h in enumerate(headers):
            sheet.write(row, col, h, fmt["th"])
        sheet.set_row(row, 20)
        row += 1

        for line in order.order_line:
            if line.display_type:
                continue

            product = line.product_id
            part_number = ""
            if product:
                part_number = (
                    getattr(product, "part_number", False)
                    or getattr(product.product_tmpl_id, "part_number", False)
                    or product.default_code
                    or ""
                )

            sheet.write(row, 0, part_number, fmt["td_text"])
            sheet.write_number(row, 1, line.product_qty or 0.0, fmt["td_qty"])
            row += 1
