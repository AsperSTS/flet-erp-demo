import flet as ft
from database import get_connection

def test_db():
    conn = get_connection()
    user = conn.execute("SELECT password_hash FROM users WHERE username=?", ("admin",)).fetchone()
    print("User admin exists:", user is not None)
    
if __name__ == "__main__":
    test_db()
