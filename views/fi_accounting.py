import flet as ft
from components.island_layout import IslandLayout, IslandCategory
from database import get_connection


class FIAccountingView(ft.Container):
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
            IslandCategory("Plan de Cuentas", ft.Icons.ACCOUNT_BALANCE, ft.Colors.GREEN_700, "Resumen y Detalles", self._build_gl_accounts),
            IslandCategory("Documentos FI", ft.Icons.RECEIPT_LONG, ft.Colors.GREEN_700, "Resumen y Detalles", self._build_fi_docs),
            IslandCategory("C x Cobrar (AR)", ft.Icons.ARROW_DOWNWARD, ft.Colors.GREEN_700, "Resumen y Detalles", self._build_ar),
            IslandCategory("C x Pagar (AP)", ft.Icons.ARROW_UPWARD, ft.Colors.GREEN_700, "Resumen y Detalles", self._build_ap),
        ]
        self.content = IslandLayout(
            title="Gestión Financiera – Contabilidad (FI)",
            icon=ft.Icons.ACCOUNT_BALANCE,
            color=ft.Colors.GREEN_700,
            categories=categories
        )
    def _build_kpis(self):
        conn = get_connection()
        ar_total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM ar_invoices WHERE status='OPEN'").fetchone()[0]
        ap_total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM ap_invoices WHERE status='OPEN'").fetchone()[0]
        doc_count = conn.execute("SELECT COUNT(*) FROM fi_documents").fetchone()[0]
        conn.close()

        def kpi(label, value, color, icon):
            return ft.Card(
                ft.Container(
                    ft.Row([
                        ft.Container(
                            ft.Icon(icon, color=ft.Colors.WHITE, size=28),
                            bgcolor=color, border_radius=10, padding=10,
                        ),
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
            kpi("AR Abierto", f"${ar_total:,.2f}", ft.Colors.BLUE_600, ft.Icons.ARROW_DOWNWARD),
            kpi("AP Abierto", f"${ap_total:,.2f}", ft.Colors.ORANGE_600, ft.Icons.ARROW_UPWARD),
            kpi("Documentos FI", str(doc_count), ft.Colors.GREEN_700, ft.Icons.RECEIPT_LONG),
        ], spacing=12)

    def _table(self, columns, rows):
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columns],
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200)),
            border_radius=8,
            heading_row_color=ft.Colors.GREEN_50,
            heading_row_height=48,
        )

    def _build_gl_accounts(self):
        conn = get_connection()
        data = conn.execute("SELECT code, name, type, currency, balance FROM gl_accounts ORDER BY code").fetchall()
        conn.close()
        type_colors = {'ASSET': ft.Colors.BLUE_700, 'LIABILITY': ft.Colors.ORANGE_700, 'EQUITY': ft.Colors.PURPLE_700, 'INCOME': ft.Colors.GREEN_700, 'EXPENSE': ft.Colors.RED_700}
        rows = []
        for r in data:
            color = type_colors.get(r[2], ft.Colors.BLUE_GREY_900)
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r[0])),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Container(ft.Text(r[2], color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD), bgcolor=color, border_radius=12, padding=ft.Padding(top=4, bottom=4, left=8, right=8))),
                ft.DataCell(ft.Text(r[3] or '')),
                ft.DataCell(ft.Text(f"${r[4]:,.2f}")),
            ]))
        t = self._table(["Cuenta", "Descripción", "Tipo", "Moneda", "Saldo"], rows)
        return ft.Container(ft.Column([ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_fi_docs(self):
        conn = get_connection()
        data = conn.execute("SELECT doc_number, doc_type, posting_date, description, total_amount, status FROM fi_documents ORDER BY id DESC LIMIT 50").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        t = self._table(["Nº Documento", "Tipo", "Fecha", "Descripción", "Total", "Estado"], rows)
        return ft.Container(ft.Column([ft.Text("Sin documentos FI registrados" if not rows else "", color=ft.Colors.BLUE_GREY_800), ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_ar(self):
        conn = get_connection()
        data = conn.execute("SELECT a.invoice_number, c.name, a.posting_date, a.due_date, a.amount, a.status FROM ar_invoices a LEFT JOIN customers c ON a.customer_id=c.id ORDER BY a.id DESC").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        t = self._table(["Factura", "Cliente", "Fecha", "Vencimiento", "Importe", "Estado"], rows)
        return ft.Container(ft.Column([ft.Text("Sin facturas AR" if not rows else "", color=ft.Colors.BLUE_GREY_800), ft.ListView([t], expand=True)], expand=True), padding=16)

    def _build_ap(self):
        conn = get_connection()
        data = conn.execute("SELECT a.invoice_number, v.name, a.posting_date, a.due_date, a.amount, a.status FROM ap_invoices a LEFT JOIN vendors v ON a.vendor_id=v.id ORDER BY a.id DESC").fetchall()
        conn.close()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(v or ''))) for v in r]) for r in data]
        t = self._table(["Factura", "Proveedor", "Fecha", "Vencimiento", "Importe", "Estado"], rows)
        return ft.Container(ft.Column([ft.Text("Sin facturas AP" if not rows else "", color=ft.Colors.BLUE_GREY_800), ft.ListView([t], expand=True)], expand=True), padding=16)
