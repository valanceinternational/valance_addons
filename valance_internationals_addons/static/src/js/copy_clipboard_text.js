/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CopyClipboardTextField extends Component {
    static template = "valance_internationals_addons.CopyClipboardTextField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.notification = useService("notification");
        this.textareaRef = useRef("textarea");
    }

    async onCopyClick() {
        const text = this.props.record.data[this.props.name] || "";
        try {
            await navigator.clipboard.writeText(text);
            this.notification.add("Copied to clipboard!", { type: "success" });
        } catch {
            const textarea = document.createElement("textarea");
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            document.body.removeChild(textarea);
            this.notification.add("Copied to clipboard!", { type: "success" });
        }
    }

    async onCopyImageClick() {
        const text = this.props.record.data[this.props.name] || "";
        if (!text) {
            this.notification.add("No data to copy.", { type: "warning" });
            return;
        }

        try {
            const rows = text.split("\n").filter((r) => r.trim());
            const tableRows = rows.map((row) => {
                const parts = row.split(" | ");
                const name = parts[0] || "";
                const qty = parts[1] ? parts[1].replace("Qty: ", "") : "";
                const amount = parts[2] ? parts[2].replace("Amount: ", "") : "";
                return { name, qty, amount };
            });

            const scale = 2;
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");

            const font = "13px Arial, sans-serif";
            const headerFont = "bold 13px Arial, sans-serif";
            const padding = 8;
            const rowHeight = 28;
            const headerHeight = 32;
            const borderColor = "#d0d0d0";
            const headerBg = "#4472C4";
            const headerFg = "#ffffff";
            const altRowBg = "#f2f2f2";
            const cellBg = "#ffffff";

            ctx.font = headerFont;
            const headers = ["Product", "Qty", "Amount"];
            const colWidths = [
                Math.max(ctx.measureText(headers[0]).width, ...tableRows.map((r) => { ctx.font = font; return ctx.measureText(r.name).width; })) + padding * 2,
                Math.max(ctx.measureText(headers[1]).width, ...tableRows.map((r) => { ctx.font = font; return ctx.measureText(r.qty).width; })) + padding * 2,
                Math.max(ctx.measureText(headers[2]).width, ...tableRows.map((r) => { ctx.font = font; return ctx.measureText(r.amount).width; })) + padding * 2,
            ];
            colWidths[0] = Math.max(colWidths[0], 180);
            colWidths[1] = Math.max(colWidths[1], 60);
            colWidths[2] = Math.max(colWidths[2], 90);

            const totalWidth = colWidths.reduce((a, b) => a + b, 0) + 1;
            const totalHeight = headerHeight + rowHeight * tableRows.length + 1;

            canvas.width = totalWidth * scale;
            canvas.height = totalHeight * scale;
            ctx.scale(scale, scale);

            // Header background
            ctx.fillStyle = headerBg;
            ctx.fillRect(0, 0, totalWidth, headerHeight);

            // Header text
            ctx.fillStyle = headerFg;
            ctx.font = headerFont;
            let x = 0;
            headers.forEach((h, i) => {
                ctx.fillText(h, x + padding, headerHeight / 2 + 5);
                x += colWidths[i];
            });

            // Header bottom border
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0, headerHeight);
            ctx.lineTo(totalWidth, headerHeight);
            ctx.stroke();

            // Data rows
            tableRows.forEach((row, ri) => {
                const y = headerHeight + ri * rowHeight;
                ctx.fillStyle = ri % 2 === 0 ? cellBg : altRowBg;
                ctx.fillRect(0, y, totalWidth, rowHeight);

                ctx.fillStyle = "#333333";
                ctx.font = font;
                let cx = 0;
                [row.name, row.qty, row.amount].forEach((val, ci) => {
                    ctx.fillText(val, cx + padding, y + rowHeight / 2 + 5);
                    cx += colWidths[ci];
                });

                // Row bottom border
                ctx.strokeStyle = borderColor;
                ctx.beginPath();
                ctx.moveTo(0, y + rowHeight);
                ctx.lineTo(totalWidth, y + rowHeight);
                ctx.stroke();
            });

            // Vertical column borders
            ctx.strokeStyle = borderColor;
            x = 0;
            for (let i = 0; i <= colWidths.length; i++) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, totalHeight);
                ctx.stroke();
                x += colWidths[i] || 0;
            }

            // Outer border
            ctx.strokeStyle = "#999999";
            ctx.strokeRect(0, 0, totalWidth, totalHeight);

            const blob = await new Promise((resolve) =>
                canvas.toBlob(resolve, "image/png")
            );
            await navigator.clipboard.write([
                new ClipboardItem({ "image/png": blob }),
            ]);
            this.notification.add("Copied as image to clipboard!", {
                type: "success",
            });
        } catch (err) {
            console.error("Copy as image failed:", err);
            this.notification.add(
                "Copy as image failed. Your browser may not support this feature.",
                { type: "danger" }
            );
        }
    }
}

export const copyClipboardTextField = {
    component: CopyClipboardTextField,
    supportedTypes: ["text"],
};

registry.category("fields").add("CopyClipboardText", copyClipboardTextField);
