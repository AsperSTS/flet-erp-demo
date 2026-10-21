import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class MMInventoryView(ft.Container):
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
            IslandCategory("Stock Actual", ft.Icons.WAREHOUSE, ft.Colors.CYAN_700, "Resumen y Detalles", self._build_stock),
            IslandCategory("Movimientos", ft.Icons.SWAP_HORIZ, ft.Colors.CYAN_700, "Resumen y Detalles", self._build_movements),
            IslandCategory("Inventario Físico", ft.Icons.FACT_CHECK, ft.Colors.CYAN_700, "Resumen y Detalles", self._build_pi),
        ]
        self.content = IslandLayout(
            title="Gestión de Inventarios (MM-IM)",
            icon=ft.Icons.WAREHOUSE,
            color=ft.Colors.CYAN_700,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        total_items = conn.execute("SELECT COUNT(*) FROM stock_balances WHERE unrestricted_qty > 0").fetchone()[0]
        total_qty = conn.execute("SELECT COALESCE(SUM(unrestricted_qty),0) FROM stock_balances").fetchone()[0]
        in_quality = conn.execute("SELECT COALESCE(SUM(quality_stock_qty),0) FROM stock_balances").fetchone()[0]
        movements = conn.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0]
        conn.close()
        def kpi(label, value, color, icon):
            return ft.Card(ft.Container(ft.Row([
                ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=26), bgcolor=color, border_radius=10, padding=10),
                ft.Column([ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_900), ft.Text(value, size=20, weight=ft.FontWeight.BOLD)], spacing=2),
            ], spacing=12), padding=16), elevation=2)
        return ft.Row([
            kpi("Posiciones con Stock", str(total_items), ft.Colors.CYAN_700, ft.Icons.INVENTORY),
            kpi("Cant. Libre Utlización", f"{total_qty:,.0f}", ft.Colors.GREEN_700, ft.Icons.WAREHOUSE),
            kpi("En Control Calidad", f"{in_quality:,.0f}", ft.Colors.ORANGE_600, ft.Icons.PENDING),
            kpi("Total Movimientos", str(movements), ft.Colors.BLUE_600, ft.Icons.SWAP_HORIZ),
        ], spacing=12, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows, border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)), border_radius=8,
            heading_row_color=ft.Colors.CYAN_50, heading_row_height=48,
        )

    def _build_stock(self):
        conn = get_connection()
        data = conn.execute("""SELECT m.code, m.description, m.unit_of_measure, p.code, w.name,
            sb.unrestricted_qty, sb.quality_stock_qty, sb.blocked_qty, sb.in_transit_qty
            FROM stock_balances sb
            JOIN materials m ON sb.material_id=m.id
            JOIN plants p ON sb.plant_id=p.id
            JOIN warehouses w ON sb.warehouse_id=w.id
            ORDER BY m.code""").fetchall()
        conn.close()
        rows = []
        for r in data:
            low = r[5] < 20
            rows.append(ft.DataRow(
                color=ft.Colors.RED_50 if low else None,
                cells=[
                    ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(r[1])),
                    ft.DataCell(ft.Text(r[2])),
                    ft.DataCell(ft.Text(r[3])),
                    ft.DataCell(ft.Text(r[4])),
                    ft.DataCell(ft.Row([
                        ft.Text(f"{r[5]:,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700 if low else ft.Colors.GREEN_800),
                        ft.Icon(ft.Icons.WARNING, size=14, color=ft.Colors.RED_600) if low else ft.Container(),
                    ])),
                    ft.DataCell(ft.Text(f"{r[6]:,.2f}")),
                    ft.DataCell(ft.Text(f"{r[7]:,.2f}")),
                    ft.DataCell(ft.Text(f"{r[8]:,.2f}")),
                ]
            ))
        t = self._table(["Material", "Descripción", "UM", "Planta", "Almacén", "Libre Utilización", "Calidad", "Bloqueado", "En Tránsito"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_movements(self):
        conn = get_connection()
        data = conn.execute("""SELECT sm.movement_number, sm.movement_type, m.code, p.code, w.name,
            sm.quantity, sm.posting_date, sm.text
            FROM stock_movements sm
            JOIN materials m ON sm.material_id=m.id
            JOIN plants p ON sm.plant_id=p.id
            LEFT JOIN warehouses w ON sm.warehouse_id=w.id
            ORDER BY sm.id DESC LIMIT 100""").fetchall()
        conn.close()
        mv_colors = {'101': ft.Colors.GREEN_700, '261': ft.Colors.ORANGE_600, '601': ft.Colors.BLUE_600}
        rows = []
        for r in data:
            color = mv_colors.get(r[1], ft.Colors.BLUE_GREY_900)
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Container(ft.Text(r[1], color=ft.Colors.WHITE, size=11), bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(r[4] or '')),
                ft.DataCell(ft.Text(f"{r[5]:,.2f}")),
                ft.DataCell(ft.Text(str(r[6])[:10])),
                ft.DataCell(ft.Text(r[7] or '')),
            ]))
        empty = ft.Text("Sin movimientos de stock", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Nº Mov.", "Tipo", "Material", "Planta", "Almacén", "Cantidad", "Fecha", "Texto"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_pi(self):
        conn = get_connection()
        data = conn.execute("""SELECT pi.pi_number, p.code, w.name, pi.count_date, pi.status
            FROM physical_inventory pi
            JOIN plants p ON pi.plant_id=p.id
            LEFT JOIN warehouses w ON pi.warehouse_id=w.id
            ORDER BY pi.id DESC""").fetchall()
        conn.close()
        sc = {'CREATED': ft.Colors.BLUE_600, 'COUNT_POSTED': ft.Colors.ORANGE_600, 'DIFFERENCES_POSTED': ft.Colors.GREEN_700}
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2] or '')),
                ft.DataCell(ft.Text(str(r[3])[:10])),
                ft.DataCell(ft.Container(ft.Text(r[4], color=ft.Colors.WHITE, size=11), bgcolor=sc.get(r[4], ft.Colors.BLUE_GREY_900), border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
            ]))
        empty = ft.Text("Sin inventarios físicos", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Nº Inventario", "Planta", "Almacén", "Fecha Conteo", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)
