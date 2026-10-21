import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class MMPurchasingView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 24

        self.bgcolor = ft.Colors.WHITE
        self.border_radius = 20
        self.shadow = ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))
        self.build_ui()


    def did_mount(self):
        self.page.pubsub.subscribe_topic("live_update", self.on_data_update)

    def will_unmount(self):
        self.page.pubsub.unsubscribe_topic("live_update")

    def on_data_update(self, topic, msg):
        if msg == 'update_data':
            self.build_ui()
            self.update()

    def build_ui(self):
        categories = [
            IslandCategory("Solicitudes de Pedido", ft.Icons.REQUEST_QUOTE, ft.Colors.BROWN_700, "Resumen y Detalles", self._build_prs),
            IslandCategory("Pedidos de Compra", ft.Icons.SHOPPING_BAG, ft.Colors.BROWN_700, "Resumen y Detalles", self._build_pos),
            IslandCategory("Entradas de Mercancía", ft.Icons.MOVE_TO_INBOX, ft.Colors.BROWN_700, "Resumen y Detalles", self._build_grs),
            IslandCategory("Facturas Proveedor", ft.Icons.RECEIPT_LONG, ft.Colors.BROWN_700, "Resumen y Detalles", self._build_ap_invoices),
        ]
        self.content = IslandLayout(
            title="Gestión de Compras y Aprovisionamiento (MM-PUR)",
            icon=ft.Icons.SHOPPING_BAG,
            color=ft.Colors.BROWN_700,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        open_pr = conn.execute("SELECT COUNT(*) FROM purchase_requests WHERE status='OPEN'").fetchone()[0]
        open_po = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM purchase_orders WHERE status='OPEN'").fetchone()
        pending_inv = conn.execute("SELECT COUNT(*) FROM ap_vendor_invoices WHERE status='OPEN'").fetchone()[0]
        conn.close()
        def kpi(label, value, color, icon):
            return ft.Card(ft.Container(ft.Row([
                ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=26), bgcolor=color, border_radius=10, padding=10),
                ft.Column([ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_900), ft.Text(value, size=20, weight=ft.FontWeight.BOLD)], spacing=2),
            ], spacing=12), padding=16), elevation=2)
        return ft.Row([
            kpi("Solicitudes Abiertas", str(open_pr), ft.Colors.ORANGE_700, ft.Icons.REQUEST_QUOTE),
            kpi("Pedidos Abiertos", str(open_po[0]), ft.Colors.BROWN_700, ft.Icons.SHOPPING_BAG),
            kpi("Monto Comprometido", f"${open_po[1]:,.2f}", ft.Colors.RED_700, ft.Icons.ATTACH_MONEY),
            kpi("Facturas Pendientes", str(pending_inv), ft.Colors.PURPLE_700, ft.Icons.RECEIPT_LONG),
        ], spacing=12, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows, border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)), border_radius=8,
            heading_row_color=ft.Colors.BROWN_50, heading_row_height=48,
        )

    def _chip(self, status, colors_map):
        color = colors_map.get(status, ft.Colors.BLUE_GREY_900)
        return ft.Container(ft.Text(status, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD), bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))

    def _build_prs(self):
        conn = get_connection()
        data = conn.execute("SELECT pr.pr_number, m.code, m.description, p.code, pr.quantity, pr.required_date, pr.requested_by, pr.status FROM purchase_requests pr LEFT JOIN materials m ON pr.material_id=m.id LEFT JOIN plants p ON pr.plant_id=p.id ORDER BY pr.id DESC").fetchall()
        conn.close()
        sc = {'OPEN': ft.Colors.BLUE_600, 'IN_PROCESS': ft.Colors.ORANGE_600, 'CLOSED': ft.Colors.GREEN_700}
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1] or '')),
                ft.DataCell(ft.Text(r[2] or '')),
                ft.DataCell(ft.Text(r[3] or '')),
                ft.DataCell(ft.Text(str(r[4]))),
                ft.DataCell(ft.Text(str(r[5] or '')[:10])),
                ft.DataCell(ft.Text(r[6] or '')),
                ft.DataCell(self._chip(r[7], sc)),
            ]))
        empty = ft.Text("Sin solicitudes de pedido", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Solicitud", "Material", "Descripción", "Planta", "Cantidad", "Fecha Req.", "Solicitante", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_pos(self):
        conn = get_connection()
        data = conn.execute("SELECT po.po_number, v.name, po.po_date, po.total_amount, po.status FROM purchase_orders po LEFT JOIN vendors v ON po.vendor_id=v.id ORDER BY po.id DESC").fetchall()
        conn.close()
        sc = {'OPEN': ft.Colors.BLUE_600, 'PARTIALLY_RECEIVED': ft.Colors.ORANGE_600, 'RECEIVED': ft.Colors.GREEN_600, 'INVOICED': ft.Colors.PURPLE_600}
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1] or '')),
                ft.DataCell(ft.Text(str(r[2])[:10])),
                ft.DataCell(ft.Text(f"${r[3]:,.2f}")),
                ft.DataCell(self._chip(r[4], sc)),
            ]))
        empty = ft.Text("Sin pedidos de compra", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Pedido", "Proveedor", "Fecha", "Importe Total", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_grs(self):
        conn = get_connection()
        data = conn.execute("SELECT gr.gr_number, gr.posting_date, gr.quantity, w.name, gr.status FROM goods_receipts gr LEFT JOIN warehouses w ON gr.warehouse_id=w.id ORDER BY gr.id DESC").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        empty = ft.Text("Sin entradas de mercancía", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Nº Entrada", "Fecha", "Cantidad", "Almacén", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_ap_invoices(self):
        conn = get_connection()
        data = conn.execute("SELECT ai.invoice_number, v.name, ai.invoice_date, ai.amount, ai.tax_amount, ai.status FROM ap_vendor_invoices ai LEFT JOIN vendors v ON ai.vendor_id=v.id ORDER BY ai.id DESC").fetchall()
        conn.close()
        sc = {'OPEN': ft.Colors.BLUE_600, 'PAID': ft.Colors.GREEN_700, 'BLOCKED': ft.Colors.RED_700}
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1] or '')),
                ft.DataCell(ft.Text(str(r[2])[:10])),
                ft.DataCell(ft.Text(f"${r[3]:,.2f}")),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
                ft.DataCell(self._chip(r[5], sc)),
            ]))
        empty = ft.Text("Sin facturas de proveedor", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Factura", "Proveedor", "Fecha", "Importe", "IVA", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)
