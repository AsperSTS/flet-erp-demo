import flet as ft

def create_sidebar(page: ft.Page, route_change_handler, current_route_ref: ft.Ref):
    # Definimos la estructura jerárquica
    groups = [
        ("General", ft.Icons.DASHBOARD, [
            ("/", "Dashboard", ft.Icons.DASHBOARD_OUTLINED),
        ]),
        ("Finanzas", ft.Icons.MONETIZATION_ON, [
            ("/fi", "Contabilidad (FI)", ft.Icons.ACCOUNT_BALANCE_OUTLINED),
            ("/co", "Controlling (CO)", ft.Icons.INSIGHTS_OUTLINED),
        ]),
        ("Logística", ft.Icons.LOCAL_SHIPPING, [
            ("/mm_materials", "Materiales (MM)", ft.Icons.INVENTORY_2_OUTLINED),
            ("/mm_purchasing", "Compras (PUR)", ft.Icons.SHOPPING_BAG_OUTLINED),
            ("/mm_inventory", "Inventarios (IM)", ft.Icons.WAREHOUSE_OUTLINED),
            ("/sd_sales", "Ventas (SD)", ft.Icons.POINT_OF_SALE_OUTLINED),
        ]),
        ("Producción", ft.Icons.FACTORY, [
            ("/pp_production", "Producción (PP)", ft.Icons.PRECISION_MANUFACTURING_OUTLINED),
            ("/pp_mrp", "MRP", ft.Icons.CALCULATE_OUTLINED),
            ("/qm_quality", "Calidad (QM)", ft.Icons.VERIFIED_OUTLINED),
        ]),
        ("Base", ft.Icons.SETTINGS_SUGGEST, [
            ("/master_data", "Datos Maestros", ft.Icons.SETTINGS_SUGGEST_OUTLINED),
            ("/settings", "Ajustes", ft.Icons.SETTINGS_OUTLINED),
        ]),
    ]
    
    sidebar_items = []
    
    def on_click(route):
        # Deselect all items visually if we were doing custom, but since we are using simple buttons:
        route_change_handler(route)

    for group_name, group_icon, items in groups:
        tiles = []
        for route, name, icon in items:
            tiles.append(
                ft.ListTile(
                    leading=ft.Icon(icon, size=20),
                    title=ft.Text(name, size=14),
                    on_click=lambda e, r=route: on_click(r)
                )
            )
            
        sidebar_items.append(
            ft.ExpansionTile(
                title=ft.Text(group_name, size=15, weight=ft.FontWeight.BOLD),
                leading=ft.Icon(group_icon, size=22, color=ft.Colors.BLUE_GREY_700),
                expanded=True if group_name == "General" else False,
                controls=tiles,
                text_color=ft.Colors.BLUE_600,
                icon_color=ft.Colors.BLUE_600
            )
        )
        
    sidebar = ft.Container(
        width=250,
        bgcolor=ft.Colors.WHITE,
        content=ft.Column(
            controls=[
                ft.Container(
                    padding=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.FINGERPRINT, size=32, color=ft.Colors.BLUE_600),
                        ft.Text("Zyra ERP", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                    ])
                ),
                ft.Divider(height=1),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        controls=sidebar_items,
                        expand=True,
                    )
                ),
                ft.Divider(height=1),
                ft.Container(
                    padding=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.LOGOUT, size=20, color=ft.Colors.RED_400),
                        ft.TextButton("Cerrar Sesión", on_click=lambda e: route_change_handler("/logout"), style=ft.ButtonStyle(color=ft.Colors.RED_400))
                    ])
                )
            ]
        ),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1),
    )
    
    return sidebar
