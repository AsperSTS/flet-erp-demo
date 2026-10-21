import flet as ft
from database import get_connection

class AccountingView(ft.Container):
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
        self.content = ft.Column([
            ft.Text("Contabilidad", size=32, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Módulo en construcción...", size=20, color=ft.Colors.BLUE_GREY_800),
            ft.Icon(ft.Icons.CONSTRUCTION, size=100, color=ft.Colors.BLUE_GREY_800)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
