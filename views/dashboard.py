import flet as ft
import math
from database import get_connection


class DashboardView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 24
        
        self.feed_messages = []
        self.build_ui()

    def did_mount(self):
        self.page.pubsub.subscribe_topic("live_update", self.on_live_update)

    def will_unmount(self):
        self.page.pubsub.unsubscribe_topic("live_update")

    def on_live_update(self, topic, msg):
        if isinstance(msg, dict) and msg.get("action") == "update_data":
            feed = msg.get("feed")
            if feed:
                self.feed_messages.insert(0, feed)
                if len(self.feed_messages) > 15:
                    self.feed_messages.pop()
            self.build_ui()
            self.update()

    def build_ui(self):
        conn = get_connection()
        total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_sales = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_orders").fetchone()[0]
        total_stock = conn.execute("SELECT COALESCE(SUM(unrestricted_qty),0) FROM stock_balances").fetchone()[0]
        
        alert_materials = conn.execute("""
            SELECT m.code, m.description, sb.unrestricted_qty, mp.reorder_point
            FROM stock_balances sb
            JOIN materials m ON sb.material_id = m.id
            JOIN material_plants mp ON m.id = mp.material_id AND sb.plant_id = mp.plant_id
            WHERE sb.unrestricted_qty <= mp.reorder_point
        """).fetchall()
        conn.close()

        def kpi_card(title, value, subtitle, icon, color):
            return ft.Card(
                elevation=4,
                shape=ft.RoundedRectangleBorder(radius=16),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, color=ft.Colors.WHITE, size=28),
                                bgcolor=color,
                                padding=12,
                                border_radius=12,
                            ),
                            ft.Column([
                                ft.Text(title, size=13, color=ft.Colors.BLUE_GREY_700, weight=ft.FontWeight.W_500),
                                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START, spacing=15),
                        ft.Text(subtitle, size=11, color=ft.Colors.BLUE_GREY_900) if subtitle else ft.Container(),
                    ], spacing=10),
                    bgcolor=ft.Colors.WHITE,
                    padding=20,
                    border_radius=16,
                ),
            )

        kpis = ft.Row([
            ft.Container(kpi_card("Clientes Activos", total_customers, "Base de datos SD", ft.Icons.PEOPLE, ft.Colors.BLUE_600), expand=1),
            ft.Container(kpi_card("Ingresos Totales", f"${total_sales:,.2f}", "Ventas acumuladas", ft.Icons.ATTACH_MONEY, ft.Colors.GREEN_600), expand=1),
            ft.Container(kpi_card("Stock Total", total_stock, "Unidades en almacenes", ft.Icons.INVENTORY, ft.Colors.ORANGE_600), expand=1),
        ], spacing=20)

        alert_rows = []
        for row in alert_materials:
            alert_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(row[0], color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(row[1], color=ft.Colors.BLUE_GREY_900)),
                    ft.DataCell(ft.Text(str(row[2]), color=ft.Colors.BLUE_GREY_900)),
                    ft.DataCell(ft.Text(str(row[3]), color=ft.Colors.BLUE_GREY_900)),
                ])
            )

        alerts_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_500),
                    ft.Text("Alertas de Inventario (Bajo Punto de Reorden)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ]),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Text("Todo el inventario está en niveles óptimos.", color=ft.Colors.BLUE_GREY_700, italic=True) if not alert_rows else ft.Container(),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Material", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)),
                        ft.DataColumn(ft.Text("Descripción", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)),
                        ft.DataColumn(ft.Text("Stock Actual", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)),
                        ft.DataColumn(ft.Text("Punto Reorden", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)),
                    ],
                    rows=alert_rows,
                    border=ft.Border(top=ft.BorderSide(1, ft.Colors.RED_100), right=ft.BorderSide(1, ft.Colors.RED_100), bottom=ft.BorderSide(1, ft.Colors.RED_100), left=ft.BorderSide(1, ft.Colors.RED_100)),
                    heading_row_color=ft.Colors.RED_50,
                    border_radius=12,
                ) if alert_rows else ft.Container()
            ], spacing=15),
            bgcolor=ft.Colors.WHITE,
            padding=25,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))
        )
        
        # Custom trend chart (Sales over last 7 days) using Containers
        bars = []
        data = [300, 450, 380, 520, 600, 490, 720]
        max_val = max(data)
        for i, val in enumerate(data):
            bars.append(
                ft.Column([
                    ft.Container(
                        width=35,
                        height=160 * (val / max_val),
                        bgcolor=ft.Colors.BLUE_500,
                        border_radius=8,
                        tooltip=f"Día {i+1}: ${val}",
                        animate=ft.Animation(500, ft.AnimationCurve.EASE_OUT)
                    ),
                    ft.Text(f"D{i+1}", size=12, color=ft.Colors.BLUE_GREY_800, weight=ft.FontWeight.W_600)
                ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        chart_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TRENDING_UP, color=ft.Colors.BLUE_600),
                    ft.Text("Tendencia de Ventas (Últimos 7 días)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    ft.Container(expand=True),
                    ft.Dropdown(
                        width=120,
                        height=35,
                        value="7d",
                        options=[ft.dropdown.Option("7d", "Últimos 7 días"), ft.dropdown.Option("30d", "Últimos 30 días")],
                        text_size=12,
                        content_padding=5,
                        border_color=ft.Colors.GREY_300,
                    )
                ]),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Container(
                    content=ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_EVENLY, vertical_alignment=ft.CrossAxisAlignment.END),
                    height=200,
                    padding=20
                )
            ], spacing=15),
            bgcolor=ft.Colors.WHITE,
            padding=25,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))
        )

        feed_list = ft.ListView(expand=True, spacing=10, auto_scroll=False)
        if not self.feed_messages:
            feed_list.controls.append(ft.Text("Esperando transacciones en vivo...", color=ft.Colors.BLUE_GREY_800, italic=True))
        else:
            for m in self.feed_messages:
                icon = ft.Icons.SHOPPING_CART if "Venta" in m else ft.Icons.INVENTORY_2
                color = ft.Colors.GREEN_600 if "Venta" in m else ft.Colors.BLUE_600
                feed_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(icon, size=16, color=color),
                            ft.Text(m, size=13, color=ft.Colors.BLUE_GREY_900)
                        ]),
                        padding=10,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                        border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200))
                    )
                )

        live_feed_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SYNC, color=ft.Colors.INDIGO_500),
                    ft.Text("Transacciones en Vivo", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.INDIGO_400)
                ]),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Container(content=feed_list, height=200)
            ], spacing=15),
            bgcolor=ft.Colors.WHITE,
            padding=25,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))
        )

        header = ft.Row([
            ft.Column([
                ft.Text("Dashboard Ejecutivo", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ft.Text("Resumen en tiempo real del estado de la empresa", size=14, color=ft.Colors.BLUE_GREY_700)
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.content = ft.Column([
            header,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            kpis,
            ft.Row([
                ft.Container(chart_card, expand=2),
                ft.Container(live_feed_card, expand=1)
            ], spacing=20),
            alerts_card
        ], expand=True, spacing=20, scroll=ft.ScrollMode.AUTO)
