import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class SDSalesView(ft.Container):
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
            IslandCategory("Pedidos de Cliente", ft.Icons.SHOPPING_CART, ft.Colors.BLUE_700, "Resumen y Detalles", self._build_orders),
            IslandCategory("Entregas", ft.Icons.LOCAL_SHIPPING, ft.Colors.BLUE_700, "Resumen y Detalles", self._build_deliveries),
            IslandCategory("Facturas SD", ft.Icons.RECEIPT, ft.Colors.BLUE_700, "Resumen y Detalles", self._build_invoices),
            IslandCategory("Clientes", ft.Icons.PEOPLE, ft.Colors.BLUE_700, "Resumen y Detalles", self._build_customers),
        ]
        self.content = IslandLayout(
            title="Ventas y Distribución (SD) – Order to Cash",
            icon=ft.Icons.POINT_OF_SALE,
            color=ft.Colors.BLUE_700,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        open_orders = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM sales_orders WHERE status='OPEN'"
        ).fetchone()
        delivered = conn.execute(
            "SELECT COUNT(*) FROM deliveries WHERE status='POSTED'"
        ).fetchone()[0]
        billed = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sd_invoices WHERE status='OPEN'"
        ).fetchone()[0]
        conn.close()

        def kpi(label, value, color, icon):
            return ft.Card(
                ft.Container(
                    ft.Row([
                        ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=26), bgcolor=color, border_radius=10, padding=10),
                        ft.Column([
                            ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_900),
                            ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                        ], spacing=2),
                    ], spacing=12),
                    padding=16,
                ),
                elevation=2,
            )

        return ft.Row([
            kpi("Pedidos Abiertos", str(open_orders[0]), ft.Colors.BLUE_600, ft.Icons.SHOPPING_CART),
            kpi("Monto Pendiente", f"${open_orders[1]:,.2f}", ft.Colors.INDIGO_600, ft.Icons.ATTACH_MONEY),
            kpi("Entregas Completadas", str(delivered), ft.Colors.GREEN_700, ft.Icons.CHECK_CIRCLE),
            kpi("Por Cobrar (SD)", f"${billed:,.2f}", ft.Colors.ORANGE_600, ft.Icons.RECEIPT),
        ], spacing=12, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=ft.Colors.BLUE_50,
            heading_row_height=48,
        )

    def _chip(self, status):
        color_map = {
            "OPEN": ft.Colors.BLUE_600,
            "PARTIALLY_DELIVERED": ft.Colors.ORANGE_600,
            "DELIVERED": ft.Colors.GREEN_600,
            "BILLED": ft.Colors.PURPLE_600,
            "CANCELLED": ft.Colors.RED_600,
            "PLANNED": ft.Colors.CYAN_700,
            "PICKED": ft.Colors.ORANGE_600,
            "POSTED": ft.Colors.GREEN_700,
        }
        color = color_map.get(status, ft.Colors.BLUE_GREY_900)
        return ft.Container(
            ft.Text(status, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
            bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8),
        )

    def _build_orders(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT so.order_number, c.name, so.order_date,
                   so.requested_delivery_date, so.total_amount, so.status
            FROM sales_orders so
            LEFT JOIN customers c ON so.customer_id = c.id
            ORDER BY so.id DESC
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1] or "")),
                ft.DataCell(ft.Text(str(r[2])[:10])),
                ft.DataCell(ft.Text(str(r[3] or "")[:10])),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
                ft.DataCell(self._chip(r[5])),
            ]))
        empty = ft.Column([
            ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=60, color=ft.Colors.GREY_300),
            ft.Text("Sin pedidos de cliente. Crea el primero.", color=ft.Colors.BLUE_GREY_800),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER) if not rows else ft.Container()
        t = self._table(["Pedido", "Cliente", "Fecha", "Entrega Req.", "Importe", "Estado"], rows)
        return ft.Container(
            ft.Column([empty, ft.ListView([t], expand=True)], expand=True,
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=16,
        )

    def _build_deliveries(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT d.delivery_number, so.order_number, p.code, d.delivery_date, d.status
            FROM deliveries d
            LEFT JOIN sales_orders so ON d.sales_order_id = so.id
            LEFT JOIN plants p ON d.plant_id = p.id
            ORDER BY d.id DESC
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1] or "")),
                ft.DataCell(ft.Text(r[2] or "")),
                ft.DataCell(ft.Text(str(r[3])[:10])),
                ft.DataCell(self._chip(r[4])),
            ]))
        empty = ft.Text("Sin entregas registradas.", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Entrega", "Pedido", "Planta", "Fecha", "Estado"], rows)
        return ft.Container(
            ft.Column([empty, ft.ListView([t], expand=True)], expand=True),
            padding=16,
        )

    def _build_invoices(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT inv.invoice_number, d.delivery_number, inv.invoice_date,
                   inv.net_amount, inv.tax_amount, inv.total_amount, inv.status
            FROM sd_invoices inv
            LEFT JOIN deliveries d ON inv.delivery_id = d.id
            ORDER BY inv.id DESC
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1] or "")),
                ft.DataCell(ft.Text(str(r[2])[:10])),
                ft.DataCell(ft.Text(f"${r[3]:,.2f}")),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
                ft.DataCell(ft.Text(f"${r[5]:,.2f}")),
                ft.DataCell(self._chip(r[6])),
            ]))
        empty = ft.Text("Sin facturas SD.", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Factura", "Entrega", "Fecha", "Neto", "IVA", "Total", "Estado"], rows)
        return ft.Container(
            ft.Column([empty, ft.ListView([t], expand=True)], expand=True),
            padding=16,
        )

    def _build_customers(self):
        conn = get_connection()
        data = conn.execute(
            "SELECT code, name, country, credit_limit, payment_terms, currency, status FROM customers ORDER BY code"
        ).fetchall()
        conn.close()
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2] or "")),
                ft.DataCell(ft.Text(f"${r[3]:,.2f}")),
                ft.DataCell(ft.Text(f"{r[4]} días")),
                ft.DataCell(ft.Text(r[5])),
                ft.DataCell(ft.Container(
                    ft.Text(r[6], color=ft.Colors.WHITE, size=11),
                    bgcolor=ft.Colors.GREEN_700 if r[6] == "ACTIVE" else ft.Colors.BLUE_GREY_900,
                    border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8),
                )),
            ]))
        t = self._table(["Código", "Nombre", "País", "Límite Crédito", "Plazo Pago", "Moneda", "Estado"], rows)
        return ft.Container(
            ft.Column([ft.ListView([t], expand=True)], expand=True),
            padding=16,
        )
