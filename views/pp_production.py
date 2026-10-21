import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class PPProductionView(ft.Container):
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
            IslandCategory("Órdenes de Producción", ft.Icons.PRECISION_MANUFACTURING, ft.Colors.DEEP_ORANGE_700, "Resumen y Detalles", self._build_orders),
            IslandCategory("Lista de Materiales (BOM)", ft.Icons.ACCOUNT_TREE, ft.Colors.DEEP_ORANGE_700, "Resumen y Detalles", self._build_bom),
            IslandCategory("Puestos de Trabajo", ft.Icons.ENGINEERING, ft.Colors.DEEP_ORANGE_700, "Resumen y Detalles", self._build_workcenters),
            IslandCategory("Hojas de Ruta", ft.Icons.ROUTE, ft.Colors.DEEP_ORANGE_700, "Resumen y Detalles", self._build_routings),
        ]
        self.content = IslandLayout(
            title="Planificación y Control de Producción (PP)",
            icon=ft.Icons.PRECISION_MANUFACTURING,
            color=ft.Colors.DEEP_ORANGE_700,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        created = conn.execute("SELECT COUNT(*) FROM production_orders WHERE status='CREATED'").fetchone()[0]
        released = conn.execute("SELECT COUNT(*) FROM production_orders WHERE status='RELEASED'").fetchone()[0]
        in_proc = conn.execute("SELECT COUNT(*) FROM production_orders WHERE status='IN_PROCESS'").fetchone()[0]
        boms = conn.execute("SELECT COUNT(*) FROM bom_headers WHERE status='ACTIVE'").fetchone()[0]
        conn.close()

        def kpi(label, value, color, icon):
            return ft.Card(ft.Container(ft.Row([
                ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=26), bgcolor=color, border_radius=10, padding=10),
                ft.Column([ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_900), ft.Text(value, size=20, weight=ft.FontWeight.BOLD)], spacing=2),
            ], spacing=12), padding=16), elevation=2)

        return ft.Row([
            kpi("Creadas", str(created), ft.Colors.BLUE_600, ft.Icons.CIRCLE_OUTLINED),
            kpi("Liberadas", str(released), ft.Colors.ORANGE_600, ft.Icons.PLAY_CIRCLE_OUTLINE),
            kpi("En Proceso", str(in_proc), ft.Colors.DEEP_ORANGE_700, ft.Icons.PENDING),
            kpi("BOMs Activos", str(boms), ft.Colors.GREEN_700, ft.Icons.ACCOUNT_TREE),
        ], spacing=12, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows, border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)), border_radius=8,
            heading_row_color=ft.Colors.DEEP_ORANGE_50, heading_row_height=48,
        )

    def _chip(self, status):
        colors = {
            'CREATED': ft.Colors.BLUE_600, 'RELEASED': ft.Colors.ORANGE_600,
            'IN_PROCESS': ft.Colors.DEEP_ORANGE_700, 'CONFIRMED': ft.Colors.GREEN_600,
            'CLOSED': ft.Colors.BLUE_GREY_900,
        }
        color = colors.get(status, ft.Colors.BLUE_GREY_900)
        return ft.Container(
            ft.Text(status, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
            bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8)
        )

    def _build_orders(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT po.order_number, m.code, m.description, p.code,
                po.planned_qty, po.confirmed_qty, po.planned_start, po.planned_finish,
                po.planned_cost, po.actual_cost, po.status
            FROM production_orders po
            JOIN materials m ON po.material_id=m.id
            JOIN plants p ON po.plant_id=p.id
            ORDER BY po.id DESC
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            dev = r[9] - r[8]
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(f"{r[4]:,.0f}")),
                ft.DataCell(ft.Text(f"{r[5]:,.0f}")),
                ft.DataCell(ft.Text(str(r[6] or '')[:10])),
                ft.DataCell(ft.Text(str(r[7] or '')[:10])),
                ft.DataCell(ft.Text(f"${r[8]:,.2f}")),
                ft.DataCell(ft.Text(f"${r[9]:,.2f}", color=ft.Colors.RED_700 if dev > 0 else ft.Colors.GREEN_700)),
                ft.DataCell(self._chip(r[10])),
            ]))
        empty = ft.Text("Sin órdenes de producción", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Orden", "Material", "Descripción", "Planta", "Cant. Plan.", "Cant. Conf.", "Inicio Plan.", "Fin Plan.", "Costo Plan.", "Costo Real", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_bom(self):
        conn = get_connection()
        boms = conn.execute("""
            SELECT bh.id, m.code, m.description, p.code, bh.base_qty, bh.status
            FROM bom_headers bh JOIN materials m ON bh.material_id=m.id JOIN plants p ON bh.plant_id=p.id
        """).fetchall()

        if not boms:
            conn.close()
            return ft.Container(ft.Column([
                ft.Icon(ft.Icons.ACCOUNT_TREE, size=60, color=ft.Colors.GREY_300),
                ft.Text("Sin listas de materiales definidas", color=ft.Colors.BLUE_GREY_800)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=40)

        tiles = []
        for bom in boms:
            items_data = conn.execute("""
                SELECT bi.item_number, c.code, c.description, bi.quantity, bi.unit, bi.item_type
                FROM bom_items bi JOIN materials c ON bi.component_id=c.id WHERE bi.bom_id=?
            """, (bom[0],)).fetchall()
            item_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in items_data]
            t = ft.DataTable(
                columns=[ft.DataColumn(ft.Text(c)) for c in ["Pos.", "Componente", "Descripción", "Cantidad", "UM", "Tipo"]],
                rows=item_rows,
                heading_row_color=ft.Colors.GREY_100,
            )
            tiles.append(ft.ExpansionTile(
                title=ft.Text(f"{bom[1]} – {bom[2]} (Planta: {bom[3]})", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"Cantidad base: {bom[4]}   Estado: {bom[5]}", size=12),
                controls=[ft.Container(t, padding=8)],
                initially_expanded=False,
            ))
        conn.close()
        return ft.Container(ft.Column(tiles, scroll=ft.ScrollMode.AUTO, expand=True), padding=16)

    def _build_workcenters(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT wc.code, wc.name, p.code, wc.capacity_hours_per_day, wc.cost_per_hour, wc.efficiency_pct
            FROM work_centers wc JOIN plants p ON wc.plant_id=p.id
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            eff_color = ft.Colors.GREEN_700 if r[5] >= 90 else (ft.Colors.ORANGE_700 if r[5] >= 70 else ft.Colors.RED_700)
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(f"{r[3]:.1f} h")),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}/h")),
                ft.DataCell(ft.Text(f"{r[5]:.0f}%", color=eff_color, weight=ft.FontWeight.BOLD)),
            ]))
        t = self._table(["Código", "Nombre", "Planta", "Cap. Diaria", "Costo/Hora", "Eficiencia"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_routings(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT m.code, m.description, p.code, r.operation_number,
                wc.name, r.description, r.setup_time_min, r.machine_time_min
            FROM routings r
            JOIN materials m ON r.material_id=m.id
            JOIN plants p ON r.plant_id=p.id
            JOIN work_centers wc ON r.work_center_id=wc.id
            ORDER BY m.code, r.operation_number
        """).fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        empty = ft.Text("Sin hojas de ruta definidas", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Material", "Descripción", "Planta", "Op.", "Puesto Trabajo", "Descripción Op.", "Prep. (min)", "Máquina (min)"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)
