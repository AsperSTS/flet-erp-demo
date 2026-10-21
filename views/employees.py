import flet as ft
from database import get_connection

class EmployeesView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 20
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
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Puesto")),
                ft.DataColumn(ft.Text("Salario"), numeric=True),
            ],
            rows=[]
        )
        self.load_data()
        
        self.content = ft.Column([
            ft.Row([
                ft.Text("Recursos Humanos", size=32, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Actualizar", icon=ft.Icons.REFRESH, on_click=lambda e: self.load_data())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.ListView(
                controls=[self.data_table],
                expand=True
            )
        ])

    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, salary FROM employees")
        rows = cursor.fetchall()
        conn.close()
        
        self.data_table.rows.clear()
        for row in rows:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row[0]))),
                        ft.DataCell(ft.Text(row[1])),
                        ft.DataCell(ft.Text(row[2])),
                        ft.DataCell(ft.Text(f"${row[3]:.2f}")),
                    ]
                )
            )
        try:
            self.update()
        except Exception:
            pass
