import flet as ft

class SettingsView(ft.Container):
    def __init__(self, theme_handler):
        super().__init__()
        self.expand = True
        self.padding = 20
        self.theme_handler = theme_handler
        self.build_ui()

    def build_ui(self):
        
        def toggle_theme(e):
            self.theme_handler()
            
        self.content = ft.Column([
            ft.Text("Ajustes del Sistema", size=32, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.DARK_MODE),
                title=ft.Text("Cambiar Tema Oscuro/Claro"),
                subtitle=ft.Text("Alterna entre el modo oscuro y el modo claro en la interfaz"),
                trailing=ft.Switch(on_change=toggle_theme)
            )
        ])
