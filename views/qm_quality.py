import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection
import datetime


class QMQualityView(ft.Container):
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
            IslandCategory("Planes de Inspección", ft.Icons.FACT_CHECK, ft.Colors.TEAL_800, "Resumen y Detalles", self._build_plans),
            IslandCategory("Lotes de Inspección", ft.Icons.SCIENCE, ft.Colors.TEAL_800, "Resumen y Detalles", self._build_lots),
            IslandCategory("Resultados", ft.Icons.ANALYTICS, ft.Colors.TEAL_800, "Resumen y Detalles", self._build_results),
        ]
        self.content = IslandLayout(
            title="Gestión de Calidad (QM)",
            icon=ft.Icons.VERIFIED,
            color=ft.Colors.TEAL_800,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        open_lots = conn.execute("SELECT COUNT(*) FROM inspection_lots WHERE status='OPEN'").fetchone()[0]
        accepted = conn.execute("SELECT COUNT(*) FROM inspection_lots WHERE status='ACCEPTED'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM inspection_lots WHERE status='REJECTED'").fetchone()[0]
        plans = conn.execute("SELECT COUNT(*) FROM inspection_plans WHERE status='ACTIVE'").fetchone()[0]
        conn.close()
        def kpi(label, value, color, icon):
            return ft.Card(ft.Container(ft.Row([
                ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=26), bgcolor=color, border_radius=10, padding=10),
                ft.Column([ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_900), ft.Text(value, size=20, weight=ft.FontWeight.BOLD)], spacing=2),
            ], spacing=12), padding=16), elevation=2)
        return ft.Row([
            kpi("Lotes Abiertos", str(open_lots), ft.Colors.BLUE_600, ft.Icons.SCIENCE),
            kpi("Aceptados", str(accepted), ft.Colors.GREEN_700, ft.Icons.CHECK_CIRCLE),
            kpi("Rechazados", str(rejected), ft.Colors.RED_700, ft.Icons.CANCEL),
            kpi("Planes Activos", str(plans), ft.Colors.TEAL_800, ft.Icons.FACT_CHECK),
        ], spacing=12, wrap=True)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows, border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)), border_radius=8,
            heading_row_color=ft.Colors.TEAL_50, heading_row_height=48,
        )

    def _chip(self, status):
        colors = {
            'OPEN': ft.Colors.BLUE_600, 'INSPECTING': ft.Colors.ORANGE_600,
            'ACCEPTED': ft.Colors.GREEN_700, 'REJECTED': ft.Colors.RED_700,
            'ACTIVE': ft.Colors.GREEN_700, 'INACTIVE': ft.Colors.BLUE_GREY_900,
            'ACCEPT': ft.Colors.GREEN_700, 'REJECT': ft.Colors.RED_700,
        }
        color = colors.get(status, ft.Colors.BLUE_GREY_900)
        return ft.Container(ft.Text(status, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD), bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))

    def _build_plans(self):
        conn = get_connection()
        data = conn.execute("""SELECT ip.plan_number, m.code, m.description, p.code,
            ip.inspection_type, ip.description, ip.status
            FROM inspection_plans ip
            JOIN materials m ON ip.material_id=m.id
            JOIN plants p ON ip.plant_id=p.id
            ORDER BY ip.id DESC""").fetchall()
        conn.close()
        type_labels = {'01': 'Entrada Compras', '03': 'Producción', '06': 'Dev. Cliente'}
        rows = []
        for r in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(type_labels.get(r[4], r[4]))),
                ft.DataCell(ft.Text(r[5] or '')),
                ft.DataCell(self._chip(r[6])),
            ]))
        empty = ft.Text("Sin planes de inspección", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Plan", "Material", "Descripción", "Planta", "Tipo Inspección", "Descripción", "Estado"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_lots(self):
        conn = get_connection()
        data = conn.execute("""SELECT il.lot_number, m.code, m.description, p.code,
            il.quantity, il.origin, il.reference_doc, il.created_date, il.status
            FROM inspection_lots il
            JOIN materials m ON il.material_id=m.id
            JOIN plants p ON il.plant_id=p.id
            ORDER BY il.id DESC""").fetchall()
        conn.close()

        def accept_lot(lot_id):
            c = get_connection()
            c.execute("UPDATE inspection_lots SET status='ACCEPTED' WHERE id=?", (lot_id,))
            c.commit()
            c.close()
            self.build_ui()
            if self.page:
                self.page.update()

        def reject_lot(lot_id):
            c = get_connection()
            c.execute("UPDATE inspection_lots SET status='REJECTED' WHERE id=?", (lot_id,))
            c.commit()
            c.close()
            self.build_ui()
            if self.page:
                self.page.update()

        rows = []
        for r in data:
            actions = ft.Row([
                ft.TextButton("✓ Aceptar", style=ft.ButtonStyle(color=ft.Colors.GREEN_700), on_click=lambda e, lid=r[0]: accept_lot(lid)),
                ft.TextButton("✗ Rechazar", style=ft.ButtonStyle(color=ft.Colors.RED_700), on_click=lambda e, lid=r[0]: reject_lot(lid)),
            ]) if r[8] == 'OPEN' else ft.Container()
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Text(r[2])),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(f"{r[4]:,.2f}")),
                ft.DataCell(ft.Text(r[5] or '')),
                ft.DataCell(ft.Text(str(r[7] or '')[:10])),
                ft.DataCell(self._chip(r[8])),
                ft.DataCell(actions),
            ]))
        empty = ft.Text("Sin lotes de inspección", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Lote", "Material", "Descripción", "Planta", "Cantidad", "Origen", "Fecha", "Estado", "Acción"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_results(self):
        conn = get_connection()
        data = conn.execute("""SELECT il.lot_number, m.code, ic.characteristic,
            ir.measured_value, ic.lower_limit, ic.upper_limit, ir.valuation, ir.recorded_at
            FROM inspection_results ir
            JOIN inspection_lots il ON ir.lot_id=il.id
            JOIN inspection_characteristics ic ON ir.characteristic_id=ic.id
            JOIN materials m ON il.material_id=m.id
            ORDER BY ir.id DESC LIMIT 100""").fetchall()
        conn.close()
        rows = []
        for r in data:
            in_spec = True
            if r[3] is not None and r[4] is not None and r[5] is not None:
                in_spec = r[4] <= r[3] <= r[5]
            rows.append(ft.DataRow(
                color=ft.Colors.RED_50 if not in_spec else None,
                cells=[
                    ft.DataCell(ft.Text(r[0])),
                    ft.DataCell(ft.Text(r[1])),
                    ft.DataCell(ft.Text(r[2])),
                    ft.DataCell(ft.Text(str(r[3]) if r[3] is not None else '-', color=ft.Colors.RED_700 if not in_spec else None, weight=ft.FontWeight.BOLD if not in_spec else None)),
                    ft.DataCell(ft.Text(str(r[4] or '-'))),
                    ft.DataCell(ft.Text(str(r[5] or '-'))),
                    ft.DataCell(self._chip(r[6])),
                    ft.DataCell(ft.Text(str(r[7] or '')[:16])),
                ]
            ))
        empty = ft.Text("Sin resultados de inspección registrados", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container()
        t = self._table(["Lote", "Material", "Característica", "Valor Medido", "Límite Inf.", "Límite Sup.", "Valoración", "Fecha"], rows)
        return ft.Container(ft.Column([empty, ft.ListView([t], expand=True)], expand=True), padding=16)

    def _create_lot_dialog(self, e):
        pass  # Dialog placeholder
