import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class MMMaterialsView(ft.Container):
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
            IslandCategory("Maestro de Materiales", ft.Icons.INVENTORY_2, ft.Colors.TEAL_700, "Resumen y Detalles", self._build_materials),
            IslandCategory("Vista de Planta (MRP)", ft.Icons.PRECISION_MANUFACTURING, ft.Colors.TEAL_700, "Resumen y Detalles", self._build_plant_view),
            IslandCategory("Valoración", ft.Icons.ATTACH_MONEY, ft.Colors.TEAL_700, "Resumen y Detalles", self._build_valuation),
        ]
        self.content = IslandLayout(
            title="Gestión de Materiales – Datos Maestros (MM)",
            icon=ft.Icons.INVENTORY_2,
            color=ft.Colors.TEAL_700,
            categories=categories
        )
    def _build_type_summary(self):
        conn = get_connection()
        data = conn.execute("SELECT material_type, COUNT(*) FROM materials GROUP BY material_type").fetchall()
        conn.close()
        labels = {
            'ROH': ('Materia Prima', ft.Colors.BLUE_600),
            'HALB': ('Semielaborado', ft.Colors.ORANGE_600),
            'FERT': ('Producto Terminado', ft.Colors.GREEN_700),
            'DIEN': ('Servicio', ft.Colors.PURPLE_600),
        }
        chips = []
        for mtype, cnt in data:
            label, color = labels.get(mtype, (mtype, ft.Colors.BLUE_GREY_900))
            chips.append(ft.Container(
                ft.Text(f"{label}: {cnt}", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                bgcolor=color, border_radius=20, padding=ft.Padding(top=8, bottom=8, left=14, right=14),
            ))
        return ft.Row(chips, spacing=8, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=ft.Colors.TEAL_50,
            heading_row_height=48,
        )

    def _build_materials(self):
        conn = get_connection()
        data = conn.execute("SELECT code, description, material_type, unit_of_measure, weight_kg, created_at FROM materials ORDER BY code").fetchall()
        conn.close()
        type_colors = {
            'ROH': ft.Colors.BLUE_600, 'HALB': ft.Colors.ORANGE_600,
            'FERT': ft.Colors.GREEN_700, 'DIEN': ft.Colors.PURPLE_600,
        }
        rows = []
        for r in data:
            color = type_colors.get(r[2], ft.Colors.BLUE_GREY_900)
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Container(
                    ft.Text(r[2], color=ft.Colors.WHITE, size=11),
                    bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8)
                )),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(f"{r[4]:.3f} kg")),
                ft.DataCell(ft.Text(str(r[5] or '')[:10])),
            ]))
        t = self._table(["Código", "Descripción", "Tipo", "UM", "Peso", "Creado"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_plant_view(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT m.code, m.description, p.code, mp.mrp_type, mp.lead_time_days,
                mp.safety_stock, mp.reorder_point, mp.lot_size
            FROM material_plants mp
            JOIN materials m ON mp.material_id=m.id
            JOIN plants p ON mp.plant_id=p.id
        """).fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        t = self._table(["Material", "Descripción", "Planta", "Tipo MRP", "Plazo Entrega", "Stock Seg.", "Punto Reord.", "Tamaño Lote"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_valuation(self):
        conn = get_connection()
        data = conn.execute("""
            SELECT m.code, m.description, p.code, mv.valuation_class, mv.price_control,
                mv.standard_price, mv.moving_avg_price
            FROM material_valuation mv
            JOIN materials m ON mv.material_id=m.id
            JOIN plants p ON mv.plant_id=p.id
        """).fetchall()
        conn.close()
        rows = []
        for r in data:
            effective_price = r[5] if r[4] == 'S' else r[6]
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(r[3] or '')),
                ft.DataCell(ft.Text('Estándar' if r[4] == 'S' else 'Prom. Móvil')),
                ft.DataCell(ft.Text(f"${effective_price:,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_700)),
            ]))
        t = self._table(["Código", "Descripción", "Planta", "Clase Val.", "Control Precio", "Precio Efectivo"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)
