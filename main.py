import flet as ft
from database import init_db, get_connection
from components.sidebar import create_sidebar
from views.dashboard import DashboardView
from views.settings import SettingsView
from views.auth import AuthView

# ERP Module views - imported lazily by name to avoid startup errors
VIEW_CLASSES = {
    "/": "DashboardView",
    "/master_data": ("views.master_data", "MasterDataView"),
    "/fi": ("views.fi_accounting", "FIAccountingView"),
    "/co": ("views.co_controlling", "COControllingView"),
    "/mm_materials": ("views.mm_materials", "MMMaterialsView"),
    "/sd_sales": ("views.sd_sales", "SDSalesView"),
    "/mm_purchasing": ("views.mm_purchasing", "MMPurchasingView"),
    "/mm_inventory": ("views.mm_inventory", "MMInventoryView"),
    "/pp_production": ("views.pp_production", "PPProductionView"),
    "/pp_mrp": ("views.pp_mrp", "PPMRPView"),
    "/qm_quality": ("views.qm_quality", "QMQualityView"),
    "/settings": "SettingsView",
}

def load_view(route, toggle_theme):
    """Lazy-load a view class and instantiate it."""
    import importlib
    if route not in VIEW_CLASSES:
        route = "/"
    if route == "/":
        return DashboardView()
    if route == "/settings":
        return SettingsView(toggle_theme)
    module_path, class_name = VIEW_CLASSES[route]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()

def main(page: ft.Page):
    # ── Page setup ──────────────────────────────────────────────────────────
    page.title = "Zyra ERP"
    page.window.width = 1280
    page.window.height = 800
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    page.fonts = {
        "Inter": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2",
        "Inter-Bold": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Bold.woff2"
    }

    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
    )
    page.dark_theme = ft.Theme(
        font_family="Inter",
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
    )
    
    page.bgcolor = ft.Colors.GREY_100

    # ── Database ─────────────────────────────────────────────────────────────
    init_db()

    # ── Auth & State ─────────────────────────────────────────────────────────
    page.session.store.set("authenticated", False)
    page.session.store.set("username", None)

    # ── Theme toggle ─────────────────────────────────────────────────────────
    def toggle_theme():
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100
        page.update()

    # ── Navigation & Layout ──────────────────────────────────────────────────
    
    # Overlay for loading state
    loading_overlay = ft.Container(
        content=ft.ProgressRing(stroke_width=3, width=40, height=40),
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        expand=True,
        visible=False,
    )
    
    main_content = ft.Container(
        expand=True,
        padding=20,
    )

    sidebar_ref = ft.Ref[ft.Container]()

    def show_loading():
        loading_overlay.visible = True
        page.update()

    def hide_loading():
        loading_overlay.visible = False
        page.update()

    def route_change(route):
        if route == "/logout":
            page.session.store.set("authenticated", False)
            page.session.store.set("username", None)
            show_auth_view()
            return

        if not page.session.store.get("authenticated"):
            show_auth_view()
            return
            
        show_loading()
        import time
        # Simulate loading for smooth UX
        time.sleep(0.3)
        
        view = load_view(route, toggle_theme)
        main_content.content = view
        hide_loading()
        page.update()

    sidebar = create_sidebar(page, route_change, sidebar_ref)
    
    app_layout = ft.Row(
        [
            sidebar,
            main_content,
        ],
        expand=True,
        spacing=0,
    )
    
    stack = ft.Stack(
        [
            app_layout,
            loading_overlay
        ],
        expand=True
    )

    def on_login_success(username):
        page.session.store.set("authenticated", True)
        page.session.store.set("username", username)
        page.controls.clear()
        page.add(stack)
        from services.live_demo import start_live_demo
        start_live_demo(page)
        route_change("/")

    def show_auth_view():
        page.controls.clear()
        page.add(AuthView(on_login_success))
        page.update()

    # Start app
    if not page.session.store.get("authenticated"):
        show_auth_view()
    else:
        page.add(stack)
        route_change("/")


if __name__ == "__main__":
    from database import init_db
    init_db()
    ft.run(main)
