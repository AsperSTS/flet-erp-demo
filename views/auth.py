import flet as ft
from database import get_connection, verify_password, hash_password

class AuthView(ft.Container):
    def __init__(self, on_login_success):
        super().__init__()
        self.expand = True
        self.on_login_success = on_login_success
        self.bgcolor = ft.Colors.BLUE_GREY_900
        self.alignment = ft.Alignment.CENTER
        self.mode = "login" # "login", "register"
        self.build_ui()

    def build_ui(self):
        self.username_field = ft.TextField(label="Usuario", prefix_icon=ft.Icons.PERSON, border_radius=12, on_submit=self.on_submit)
        self.password_field = ft.TextField(label="Contraseña", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, border_radius=12, on_submit=self.on_submit)
        
        self.error_text = ft.Text(color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.W_500)
        self.loading_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
        self.submit_btn = ft.ElevatedButton("Iniciar Sesión", on_click=self.on_submit, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
        
        self.toggle_btn = ft.TextButton("¿No tienes cuenta? Regístrate", on_click=lambda e: self.toggle_mode("register"))
        self.forgot_btn = ft.TextButton("¿Olvidaste tu contraseña?", on_click=lambda e: self.toggle_mode("reset"))

        self.card = ft.Card(
            elevation=10,
            shape=ft.RoundedRectangleBorder(radius=20),
            bgcolor=ft.Colors.WHITE,
            content=ft.Container(
                padding=40,
                width=400,
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.FINGERPRINT, size=60, color=ft.Colors.BLUE_700),
                        ft.Text("Zyra ERP", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                        ft.Container(
                            content=ft.Text("Inicia sesión para continuar", size=14, color=ft.Colors.BLUE_GREY_900),
                            margin=ft.Margin(0, 0, 0, 20)
                        ),
                        self.error_text,
                        self.username_field,
                        self.password_field,
                        ft.Row([self.loading_ring, self.submit_btn], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([self.toggle_btn, self.forgot_btn], alignment=ft.MainAxisAlignment.CENTER, wrap=True)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                )
            )
        )
        self.content = self.card

    def toggle_mode(self, new_mode):
        self.mode = new_mode
        self.error_text.value = ""
        self.username_field.visible = True
        self.password_field.visible = True
        self.forgot_btn.visible = True
        
        if self.mode == "register":
            self.submit_btn.text = "Crear Cuenta"
            self.toggle_btn.text = "¿Ya tienes cuenta? Inicia sesión"
            self.toggle_btn.on_click = lambda e: self.toggle_mode("login")
        elif self.mode == "reset":
            self.submit_btn.text = "Restaurar"
            self.password_field.visible = False
            self.forgot_btn.visible = False
            self.toggle_btn.text = "Volver al Login"
            self.toggle_btn.on_click = lambda e: self.toggle_mode("login")
            self.error_text.color = ft.Colors.BLUE_600
            self.error_text.value = "Ingresa tu usuario para restablecer credenciales"
        else:
            self.mode = "login"
            self.submit_btn.text = "Iniciar Sesión"
            self.toggle_btn.text = "¿No tienes cuenta? Regístrate"
            self.toggle_btn.on_click = lambda e: self.toggle_mode("register")
            self.error_text.color = ft.Colors.RED_400
        
        self.update()

    def on_submit(self, e):
        username = (self.username_field.value or "").strip()
        password = (self.password_field.value or "").strip()

        if not username:
            self.error_text.value = "Ingresa tu usuario"
            self.update()
            return
            
        if self.mode != "reset" and not password:
            self.error_text.value = "Ingresa tu contraseña"
            self.update()
            return

        self.submit_btn.disabled = True
        self.loading_ring.visible = True
        self.update()

        conn = get_connection()
        try:
            if self.mode == "login":
                user = conn.execute("SELECT password_hash FROM users WHERE username=?", (username,)).fetchone()
                if user and verify_password(password, user[0]):
                    self.on_login_success(username)
                else:
                    self.error_text.value = "Credenciales incorrectas"
            elif self.mode == "reset":
                user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
                if user:
                    self.error_text.color = ft.Colors.GREEN_600
                    self.error_text.value = f"¡Enlace de recuperación enviado a {username}!"
                else:
                    self.error_text.color = ft.Colors.RED_400
                    self.error_text.value = "El usuario no existe"
            else:
                # Register
                user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
                if user:
                    self.error_text.color = ft.Colors.RED_400
                    self.error_text.value = "El usuario ya existe"
                else:
                    hashed = hash_password(password)
                    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
                    conn.commit()
                    self.on_login_success(username)
        except Exception as ex:
            self.error_text.color = ft.Colors.RED_400
            self.error_text.value = f"Error: {ex}"
        finally:
            conn.close()
            if self.page:
                self.submit_btn.disabled = False
                self.loading_ring.visible = False
                self.update()
