import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class COControllingView(ft.Container):
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
            IslandCategory("Centros de Costo", ft.Icons.ACCOUNT_TREE, ft.Colors.PURPLE_700, "Resumen y Detalles", self._build_cost_centers),
            IslandCategory("Órdenes Internas", ft.Icons.WORK_HISTORY, ft.Colors.PURPLE_700, "Resumen y Detalles", self._build_internal_orders),
            IslandCategory("Imputaciones CO", ft.Icons.INSIGHTS, ft.Colors.PURPLE_700, "Resumen y Detalles", self._build_postings),
        ]
        self.content = IslandLayout(
            title="Controlling – Contabilidad de Costos (CO)",
            icon=ft.Icons.INSIGHTS,
            color=ft.Colors.PURPLE_700,
            categories=categories
        )
    def _table(self, columns, rows, header_color=None):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=header_color or ft.Colors.PURPLE_50,
            heading_row_height=48,
        )

    def _build_cost_centers(self):
        conn = get_connection()
        data = conn.execute("SELECT cc.code, cc.name, cc.type, c.name, COALESCE(SUM(cp.amount),0) FROM cost_centers cc LEFT JOIN companies c ON cc.company_id=c.id LEFT JOIN co_postings cp ON cp.cost_center_id=cc.id GROUP BY cc.id").fetchall()
        conn.close()
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2] or '')),
                ft.DataCell(ft.Text(r[3] or '')),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
            ]))
        t = self._table(["Código", "Nombre", "Tipo", "Empresa", "Costo Real Acum."], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_internal_orders(self):
        conn = get_connection()
        data = conn.execute("SELECT io.code, io.description, cc.name, io.budget, io.actual_cost, io.status FROM internal_orders io LEFT JOIN cost_centers cc ON io.cost_center_id=cc.id").fetchall()
        conn.close()
        status_colors = {'OPEN': ft.Colors.GREEN_700, 'CLOSED': ft.Colors.BLUE_GREY_900}
        rows = []
        for r in data:
            sc = status_colors.get(r[5], ft.Colors.ORANGE_700)
            deviation = r[4] - r[3]
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2] or '')),
                ft.DataCell(ft.Text(f"${r[3]:,.2f}")),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
                ft.DataCell(ft.Text(f"${deviation:,.2f}", color=ft.Colors.RED_700 if deviation > 0 else ft.Colors.GREEN_700)),
                ft.DataCell(ft.Container(ft.Text(r[5], color=ft.Colors.WHITE, size=11), bgcolor=sc, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
            ]))
        empty = ft.Text("Sin órdenes internas registradas", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Código", "Descripción", "Centro Costo", "Presupuesto", "Costo Real", "Desviación", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_postings(self):
        conn = get_connection()
        data = conn.execute("SELECT p.posting_date, cc.name, p.cost_element, p.amount, p.text FROM co_postings p LEFT JOIN cost_centers cc ON p.cost_center_id=cc.id ORDER BY p.id DESC LIMIT 50").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        empty = ft.Text("Sin imputaciones CO", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Fecha", "Centro Costo", "Elemento Costo", "Importe", "Texto"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)
