import flet as ft

class IslandCategory:
    def __init__(self, title, icon, color, subtitle="", content_view=None):
        self.title = title
        self.icon = icon
        self.color = color
        self.subtitle = subtitle
        self.content_view = content_view

class IslandLayout(ft.Container):
    def __init__(self, title, icon, color, categories):
        super().__init__()
        self.expand = True
        self.padding = 24
        
        self.main_title = title
        self.main_icon = icon
        self.main_color = color
        self.categories = categories
        
        self.current_view = "categories"
        self.selected_category = None
        self.build_ui()

    def build_ui(self):
        # Header (Breadcrumb)
        self.header_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.update_header()
        
        # Content Container
        self.content_container = ft.Container(expand=True)
        self.update_content()
        
        self.content = ft.Column([
            self.header_row,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            self.content_container
        ], expand=True, spacing=20)

    def update_header(self):
        self.header_row.controls.clear()
        
        # Root breadcrumb
        root_btn = ft.TextButton(
            content=ft.Row([
                ft.Icon(self.main_icon, color=self.main_color, size=24),
                ft.Text(self.main_title, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
            ], spacing=8),
            on_click=lambda e: self.go_back(),
            style=ft.ButtonStyle(overlay_color=ft.Colors.TRANSPARENT)
        )
        self.header_row.controls.append(root_btn)
        
        # Subcategory breadcrumb
        if self.current_view == "subcategory" and self.selected_category:
            self.header_row.controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.BLUE_GREY_800))
            self.header_row.controls.append(
                ft.Row([
                    ft.Icon(self.selected_category.icon, color=self.selected_category.color, size=20),
                    ft.Text(self.selected_category.title, size=18, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_GREY_800)
                ], spacing=6)
            )

    def update_content(self):
        if self.current_view == "categories":
            cards = []
            for cat in self.categories:
                # Create Island Card
                card = ft.Card(
                    elevation=4,
                    shape=ft.RoundedRectangleBorder(radius=16),
                    bgcolor=ft.Colors.WHITE,
                    content=ft.Container(
                        padding=20,
                        width=250,
                        height=160,
                        ink=True,
                        on_click=self._make_nav_handler(cat),
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(cat.icon, color=ft.Colors.WHITE, size=32),
                                bgcolor=cat.color,
                                padding=12,
                                border_radius=12,
                            ),
                            ft.Text(cat.title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                            ft.Text(cat.subtitle, size=12, color=ft.Colors.BLUE_GREY_900)
                        ], spacing=10, alignment=ft.MainAxisAlignment.START)
                    )
                )
                cards.append(card)
            
            self.content_container.content = ft.Row(
                cards,
                wrap=True,
                spacing=20,
                run_spacing=20,
                alignment=ft.MainAxisAlignment.START
            )
        else:
            if self.selected_category and self.selected_category.content_view:
                self.content_container.content = self.selected_category.content_view()
            else:
                self.content_container.content = ft.Text("No content available", color=ft.Colors.RED)

    def _make_nav_handler(self, cat):
        def handler(e):
            self.selected_category = cat
            self.current_view = "subcategory"
            self.update_header()
            self.update_content()
            self.update()
        return handler

    def go_back(self):
        if self.current_view != "categories":
            self.selected_category = None
            self.current_view = "categories"
            self.update_header()
            self.update_content()
            self.update()
