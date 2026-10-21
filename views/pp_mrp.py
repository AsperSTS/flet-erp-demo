import flet as ft
from database import get_connection
import datetime


class PPMRPView(ft.Container):
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
        self.run_output = ft.Ref[ft.Column]()
        self.proposals_table_ref = ft.Ref[ft.ListView]()
        self.content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CALCULATE, size=36, color=ft.Colors.INDIGO_700),
                ft.Column([
                    ft.Text("Planificación de Necesidades de Material (MRP)", size=26, weight=ft.FontWeight.BOLD),
                    ft.Text("MRP Run: cálculo automático de propuestas de aprovisionamiento", size=13, color=ft.Colors.BLUE_GREY_900),
                ], spacing=2),
            ], spacing=12),
            ft.Divider(height=1),
            self._build_run_panel(),
            ft.Divider(height=1),
            self._build_proposals(),
        ], spacing=16, expand=True)

    def _build_run_panel(self):
        conn = get_connection()
        plants = conn.execute("SELECT id, code, name FROM plants").fetchall()
        last_runs = conn.execute("SELECT mr.run_date, p.code, mr.scope, mr.status, mr.proposals_created FROM mrp_runs mr JOIN plants p ON mr.plant_id=p.id ORDER BY mr.id DESC LIMIT 5").fetchall()
        conn.close()

        plant_options = [ft.dropdown.Option(str(p[0]), f"{p[1]} – {p[2]}") for p in plants]
        plant_dd = ft.Dropdown(label="Planta", options=plant_options, width=250, value=str(plants[0][0]) if plants else None)

        run_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in last_runs]
        run_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in ["Fecha", "Planta", "Alcance", "Estado", "Propuestas"]],
            rows=run_rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=ft.Colors.INDIGO_50,
        )

        def run_mrp(e):
            if not plant_dd.value:
                return
            plant_id = int(plant_dd.value)
            conn2 = get_connection()
            today = datetime.date.today().isoformat()

            # Leer materiales con MRP activo en la planta
            materials = conn2.execute(
                "SELECT mp.material_id, m.code, mp.reorder_point, mp.lead_time_days, mp.safety_stock FROM material_plants mp JOIN materials m ON mp.material_id=m.id WHERE mp.plant_id=? AND mp.mrp_type='PD'",
                (plant_id,)
            ).fetchall()

            proposals_created = 0
            run_id = conn2.execute(
                "INSERT INTO mrp_runs (run_date, plant_id, scope, status, proposals_created) VALUES (?, ?, 'TOTAL', 'RUNNING', 0)",
                (today, plant_id)
            ).lastrowid

            for mat in materials:
                mat_id, mat_code, reorder_point, lead_time, safety_stock = mat
                # Get current stock
                stock_row = conn2.execute(
                    "SELECT COALESCE(SUM(unrestricted_qty),0) FROM stock_balances WHERE material_id=? AND plant_id=?",
                    (mat_id, plant_id)
                ).fetchone()[0]

                # If stock below reorder point -> create PR proposal
                if stock_row <= reorder_point:
                    propose_qty = max((reorder_point + safety_stock) - stock_row, safety_stock)
                    req_date = (datetime.date.today() + datetime.timedelta(days=lead_time)).isoformat()
                    conn2.execute(
                        "INSERT INTO mrp_proposals (mrp_run_id, material_id, plant_id, proposal_type, quantity, required_date, created_date, status) VALUES (?, ?, ?, 'PR', ?, ?, ?, 'OPEN')",
                        (run_id, mat_id, plant_id, propose_qty, req_date, today)
                    )
                    proposals_created += 1

            conn2.execute("UPDATE mrp_runs SET status='COMPLETED', proposals_created=? WHERE id=?", (proposals_created, run_id))
            conn2.commit()
            conn2.close()
            self.build_ui()
            if self.page:
                self.page.update()

        return ft.Card(
            ft.Container(
                ft.Column([
                    ft.Text("Ejecutar Corrida MRP", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([plant_dd, ft.ElevatedButton("▶ Ejecutar MRP", bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE, on_click=run_mrp)], spacing=16),
                    ft.Divider(),
                    ft.Text("Últimas Corridas", size=14, weight=ft.FontWeight.BOLD),
                    run_table if run_rows else ft.Text("Sin corridas previas", color=ft.Colors.BLUE_GREY_800),
                ], spacing=12),
                padding=20,
            ),
            elevation=2,
        )

    def _build_proposals(self):
        conn = get_connection()
        data = conn.execute(
            """SELECT mp.id, mr.run_date, m.code, m.description, p.code, mp.proposal_type,
                mp.quantity, mp.required_date, mp.created_date, mp.status
                FROM mrp_proposals mp
                JOIN mrp_runs mr ON mp.mrp_run_id=mr.id
                JOIN materials m ON mp.material_id=m.id
                JOIN plants p ON mp.plant_id=p.id
                ORDER BY mp.id DESC LIMIT 100"""
        ).fetchall()
        conn.close()

        def convert_proposal(e, prop_id):
            conn3 = get_connection()
            conn3.execute("UPDATE mrp_proposals SET status='CONVERTED' WHERE id=?", (prop_id,))
            conn3.commit()
            conn3.close()
            self.build_ui()
            if self.page:
                self.page.update()

        rows = []
        for r in data:
            sc = {'OPEN': ft.Colors.BLUE_600, 'CONVERTED': ft.Colors.GREEN_700, 'CANCELLED': ft.Colors.RED_700}
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(r[1])[:10])),
                ft.DataCell(ft.Text(r[2], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r[3])),
                ft.DataCell(ft.Text(r[4])),
                ft.DataCell(ft.Container(ft.Text(r[5], color=ft.Colors.WHITE, size=11), bgcolor=ft.Colors.INDIGO_700, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
                ft.DataCell(ft.Text(f"{r[6]:,.2f}")),
                ft.DataCell(ft.Text(str(r[7] or '')[:10])),
                ft.DataCell(ft.Container(ft.Text(r[9], color=ft.Colors.WHITE, size=11), bgcolor=sc.get(r[9], ft.Colors.BLUE_GREY_900), border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
                ft.DataCell(ft.TextButton("Convertir →", on_click=lambda e, pid=r[0]: convert_proposal(e, pid)) if r[9] == 'OPEN' else ft.Text("", size=12, color=ft.Colors.BLUE_GREY_800)),
            ]))

        t = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in ["Corrida", "Material", "Descripción", "Planta", "Tipo", "Cantidad", "Fecha Req.", "Estado", "Acción"]],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=ft.Colors.INDIGO_50,
            heading_row_height=48,
        )

        return ft.Column([
            ft.Text("Propuestas MRP", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Sin propuestas. Ejecuta una corrida MRP para generarlas.", color=ft.Colors.BLUE_GREY_800) if not rows else ft.Container(),
            ft.ListView([t], expand=True) if rows else ft.Container(),
        ], expand=True, spacing=8)
