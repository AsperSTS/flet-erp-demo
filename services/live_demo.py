import threading
import time
import random
import datetime
from database import get_connection

_running = False

def generate_random_sales_order(conn):
    try:
        cursor = conn.cursor()
        customers = cursor.execute("SELECT id FROM customers").fetchall()
        materials = cursor.execute("""
            SELECT m.id, m.description, COALESCE(mv.standard_price, 100.0)
            FROM materials m
            LEFT JOIN material_valuation mv ON m.id = mv.material_id
        """).fetchall()
        
        if not customers or not materials:
            return None
            
        customer_id = random.choice(customers)[0]
        material = random.choice(materials)
        qty = random.randint(1, 100)
        price = material[2] * 1.1
        total = qty * price
        
        order_number = f"SO-{random.randint(10000, 99999)}"
        today = datetime.date.today().isoformat()
        
        # INSERT INTO sales_orders
        cursor.execute("INSERT INTO sales_orders (order_number, customer_id, order_date, total_amount) VALUES (?, ?, ?, ?)",
                      (order_number, customer_id, today, total))
        conn.commit()
        
        # ar_invoices needs posting_date, due_date, status according to schema? Let's check schema.
        # It's probably just basic fields, wait, if ar_invoices requires posting_date:
        inv_number = f"INV-{random.randint(10000, 99999)}"
        cursor.execute("INSERT INTO ar_invoices (invoice_number, customer_id, posting_date, due_date, amount, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (inv_number, customer_id, today, today, total, 'OPEN'))
        conn.commit()
        return f"Nueva Venta Creada: {order_number} por ${total:,.2f}"
    except Exception as e:
        print(f"Error generating sales order: {e}")
        return None

def generate_random_inventory_movement(conn):
    try:
        cursor = conn.cursor()
        materials = cursor.execute("SELECT id, description FROM materials").fetchall()
        plants = cursor.execute("SELECT id FROM plants").fetchall()
        warehouses = cursor.execute("SELECT id FROM warehouses").fetchall()
        if not materials or not plants or not warehouses:
            return None
            
        mat = random.choice(materials)
        plant_id = random.choice(plants)[0]
        wh_id = random.choice(warehouses)[0]
        qty = random.randint(10, 500)
        movement_type = random.choice(["101 (Entrada GR)", "201 (Salida Centro Costo)", "261 (Salida Orden Prod)", "601 (Salida Venta)"])
        
        mov_number = f"MOV-{random.randint(10000, 99999)}"
        today = datetime.date.today().isoformat()
        
        cursor.execute("INSERT INTO stock_movements (movement_number, movement_type, material_id, plant_id, warehouse_id, quantity, posting_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (mov_number, movement_type, mat[0], plant_id, wh_id, qty, today))
        conn.commit()
        return f"Movimiento de Inventario: {movement_type} - {qty}x {mat[1]}"
    except Exception as e:
        print(f"Error generating inventory movement: {e}")
        return None

def live_data_loop(page):
    global _running
    conn = get_connection()
    while _running:
        time.sleep(random.randint(5, 25))
        
        msg = None
        choice = random.random()
        if choice > 0.5:
            msg = generate_random_sales_order(conn)
        else:
            msg = generate_random_inventory_movement(conn)
            
        if msg:
            # Tell all connected clients to update their views and send the feed message
            page.pubsub.send_all_on_topic("live_update", {"action": "update_data", "feed": msg})
        
    conn.close()

def start_live_demo(page):
    global _running
    if _running:
        return
    _running = True
    t = threading.Thread(target=live_data_loop, args=(page,), daemon=True)
    t.start()
    print("Live demo simulator started.")

def stop_live_demo():
    global _running
    _running = False
    print("Live demo simulator stopping...")
