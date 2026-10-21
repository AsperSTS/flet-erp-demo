import flet as ft

class BaseERPView(ft.Container):
    def __init__(self, title, subtitle, icon, content_controls):
        super().__init__()
        self.expand = True
        self.padding = 24
        self._content_controls = content_controls
        
        header = ft.Row([
            ft.Icon(icon, size=36, color=ft.Colors.BLUE_600),
            ft.Column([
                ft.Text(title, size=26, weight=ft.FontWeight.W_800, color=ft.Colors.BLUE_GREY_900),
                ft.Text(subtitle, size=13, color=ft.Colors.BLUE_GREY_800),
            ], spacing=2),
        ], spacing=15)
        
        island_card = ft.Container(
            content=ft.Column(
                [header, ft.Divider(height=1, color=ft.Colors.GREY_100)] + self._content_controls,
                spacing=20,
                expand=True
            ),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=20,
            expand=True,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))
        )
        
        self.content = island_card
        
    def did_mount(self):
        self.page.pubsub.subscribe_topic("live_update", self.on_live_update)
        self.load_data()

    def will_unmount(self):
        self.page.pubsub.unsubscribe_topic("live_update")

    def on_live_update(self, topic, msg):
        self.load_data()
        
    def load_data(self):
        # To be overridden by subclasses
        pass
