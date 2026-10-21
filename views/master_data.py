import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class MasterDataView(ft.Container):
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
            IslandCategory("Empresas", ft.Icons.BUSINESS, ft.Colors.INDIGO_600, "Resumen y Detalles", self._build_companies),
            IslandCategory("Plantas / Almacenes", ft.Icons.FACTORY, ft.Colors.INDIGO_600, "Resumen y Detalles", self._build_plants),
            IslandCategory("Centros de Costo", ft.Icons.ACCOUNT_TREE, ft.Colors.INDIGO_600, "Resumen y Detalles", self._build_cost_centers),
            IslandCategory("Proveedores", ft.Icons.LOCAL_SHIPPING, ft.Colors.INDIGO_600, "Resumen y Detalles", self._build_vendors),
        ]
        self.content = IslandLayout(
            title="Datos Maestros Fundamentales",
            icon=ft.Icons.SETTINGS_SUGGEST,
            color=ft.Colors.INDIGO_600,
            categories=categories
        )
    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
            heading_row_color=ft.Colors.INDIGO_50,
            heading_row_height=48,
        )

    def _build_companies(self):
        conn = get_connection()
        rows_data = conn.execute("SELECT code, name, country, currency, fiscal_year_start FROM companies").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in rows_data]
        t = self._table(["Código", "Razón Social", "País", "Moneda", "Inicio Ejercicio"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_plants(self):
        conn = get_connection()
        plants = conn.execute("SELECT p.code, p.name, c.name, p.address FROM plants p LEFT JOIN companies c ON p.company_id=c.id").fetchall()
        warehouses = conn.execute("SELECT w.code, w.name, p.code FROM warehouses w LEFT JOIN plants p ON w.plant_id=p.id").fetchall()
        conn.close()
        p_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in plants]
        w_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in warehouses]
        return ft.Container(
            ft.Column([
                ft.Text("Plantas", weight=ft.FontWeight.BOLD, size=15),
                ft.ListView([self._table(["Código", "Nombre", "Empresa", "Dirección"], p_rows)], expand=True, auto_scroll=False),
                ft.Divider(),
                ft.Text("Almacenes", weight=ft.FontWeight.BOLD, size=15),
                ft.ListView([self._table(["Código", "Nombre", "Planta"], w_rows)], expand=True, auto_scroll=False),
            ], spacing=10, expand=True),
            padding=16,
        )

    def _build_cost_centers(self):
        conn = get_connection()
        rows_data = conn.execute("SELECT cc.code, cc.name, cc.type, c.name FROM cost_centers cc LEFT JOIN companies c ON cc.company_id=c.id").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in rows_data]
        t = self._table(["Código", "Nombre", "Tipo", "Empresa"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_vendors(self):
        conn = get_connection()
        rows_data = conn.execute("SELECT code, name, country, payment_terms, currency FROM vendors").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in rows_data]
        t = self._table(["Código", "Nombre", "País", "Plazo Pago (días)", "Moneda"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)
