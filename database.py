import sqlite3

DB_NAME = "erp_database.sqlite3"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ─────────────────────────────────────────────
    # 0. SEGURIDAD Y USUARIOS
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'USER'
    )''')
    
    # Seed admin user if it doesn't exist
    admin_user = cursor.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not admin_user:
        hashed = hash_password("admin")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", hashed, "ADMIN"))
        conn.commit()

    # ─────────────────────────────────────────────
    # 1. DATOS MAESTROS FUNDAMENTALES
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        country TEXT,
        currency TEXT DEFAULT 'MXN',
        fiscal_year_start TEXT DEFAULT '01-01'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        company_id INTEGER REFERENCES companies(id),
        address TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        plant_id INTEGER REFERENCES plants(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS cost_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        company_id INTEGER REFERENCES companies(id),
        type TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        country TEXT,
        payment_terms INTEGER DEFAULT 30,
        currency TEXT DEFAULT 'MXN',
        email TEXT,
        phone TEXT
    )''')

    # ─────────────────────────────────────────────
    # 2. FI – CONTABILIDAD GENERAL
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS gl_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,  -- ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
        company_id INTEGER REFERENCES companies(id),
        currency TEXT DEFAULT 'MXN',
        balance REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fi_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_number TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,  -- SA, KR, DR, etc
        posting_date TEXT NOT NULL,
        reference TEXT,
        description TEXT,
        company_id INTEGER REFERENCES companies(id),
        total_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'POSTED'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fi_line_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER REFERENCES fi_documents(id),
        gl_account_id INTEGER REFERENCES gl_accounts(id),
        debit REAL DEFAULT 0.0,
        credit REAL DEFAULT 0.0,
        cost_center_id INTEGER REFERENCES cost_centers(id),
        text TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ar_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER REFERENCES customers(id),
        posting_date TEXT NOT NULL,
        due_date TEXT,
        amount REAL NOT NULL,
        tax_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'OPEN',  -- OPEN, PAID, OVERDUE
        fi_document_id INTEGER REFERENCES fi_documents(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ap_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        vendor_id INTEGER REFERENCES vendors(id),
        posting_date TEXT NOT NULL,
        due_date TEXT,
        amount REAL NOT NULL,
        tax_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'OPEN',  -- OPEN, PAID, BLOCKED
        fi_document_id INTEGER REFERENCES fi_documents(id)
    )''')

    # ─────────────────────────────────────────────
    # 3. CO – CONTROLLING
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS internal_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        cost_center_id INTEGER REFERENCES cost_centers(id),
        budget REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0,
        status TEXT DEFAULT 'OPEN'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS co_postings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        posting_date TEXT NOT NULL,
        cost_center_id INTEGER REFERENCES cost_centers(id),
        internal_order_id INTEGER REFERENCES internal_orders(id),
        cost_element TEXT NOT NULL,
        amount REAL NOT NULL,
        text TEXT,
        fi_document_id INTEGER REFERENCES fi_documents(id)
    )''')

    # ─────────────────────────────────────────────
    # 4. MM – DATOS MAESTROS DE MATERIAL
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        material_type TEXT NOT NULL,  -- ROH, HALB, FERT, DIEN
        unit_of_measure TEXT DEFAULT 'PZA',
        weight_kg REAL DEFAULT 0.0,
        category TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS material_plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        mrp_type TEXT DEFAULT 'PD',
        lead_time_days INTEGER DEFAULT 7,
        safety_stock REAL DEFAULT 0.0,
        reorder_point REAL DEFAULT 0.0,
        lot_size TEXT DEFAULT 'EX',
        UNIQUE(material_id, plant_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS material_valuation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        valuation_class TEXT,
        price_control TEXT DEFAULT 'S',  -- S=Standard, V=Moving Average
        standard_price REAL DEFAULT 0.0,
        moving_avg_price REAL DEFAULT 0.0,
        UNIQUE(material_id, plant_id)
    )''')

    # ─────────────────────────────────────────────
    # 5. SD – VENTAS Y DISTRIBUCIÓN
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        country TEXT,
        credit_limit REAL DEFAULT 0.0,
        payment_terms INTEGER DEFAULT 30,
        currency TEXT DEFAULT 'MXN',
        email TEXT,
        phone TEXT,
        status TEXT DEFAULT 'ACTIVE'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sales_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER REFERENCES customers(id),
        order_date TEXT NOT NULL,
        requested_delivery_date TEXT,
        status TEXT DEFAULT 'OPEN',  -- OPEN, PARTIALLY_DELIVERED, DELIVERED, BILLED, CANCELLED
        payment_terms INTEGER DEFAULT 30,
        total_amount REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sales_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sales_order_id INTEGER REFERENCES sales_orders(id),
        item_number INTEGER NOT NULL,
        material_id INTEGER REFERENCES materials(id),
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        discount_pct REAL DEFAULT 0.0,
        delivered_qty REAL DEFAULT 0.0,
        status TEXT DEFAULT 'OPEN'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delivery_number TEXT UNIQUE NOT NULL,
        sales_order_id INTEGER REFERENCES sales_orders(id),
        plant_id INTEGER REFERENCES plants(id),
        delivery_date TEXT NOT NULL,
        status TEXT DEFAULT 'PLANNED'  -- PLANNED, PICKED, POSTED
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sd_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        delivery_id INTEGER REFERENCES deliveries(id),
        invoice_date TEXT NOT NULL,
        net_amount REAL NOT NULL,
        tax_amount REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'OPEN'
    )''')

    # ─────────────────────────────────────────────
    # 6. MM-PUR – COMPRAS Y APROVISIONAMIENTO
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchase_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pr_number TEXT UNIQUE NOT NULL,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        quantity REAL NOT NULL,
        required_date TEXT,
        requested_by TEXT,
        status TEXT DEFAULT 'OPEN',  -- OPEN, IN_PROCESS, CLOSED
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        vendor_id INTEGER REFERENCES vendors(id),
        po_date TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN',  -- OPEN, PARTIALLY_RECEIVED, RECEIVED, INVOICED
        total_amount REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS po_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_order_id INTEGER REFERENCES purchase_orders(id),
        item_number INTEGER NOT NULL,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        received_qty REAL DEFAULT 0.0,
        invoiced_qty REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS goods_receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gr_number TEXT UNIQUE NOT NULL,
        po_item_id INTEGER REFERENCES po_items(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        quantity REAL NOT NULL,
        posting_date TEXT NOT NULL,
        status TEXT DEFAULT 'POSTED'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ap_vendor_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        vendor_id INTEGER REFERENCES vendors(id),
        purchase_order_id INTEGER REFERENCES purchase_orders(id),
        invoice_date TEXT NOT NULL,
        amount REAL NOT NULL,
        tax_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'OPEN'  -- OPEN, PAID, BLOCKED
    )''')

    # ─────────────────────────────────────────────
    # 7. MM-IM – GESTIÓN DE INVENTARIOS
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        unrestricted_qty REAL DEFAULT 0.0,
        quality_stock_qty REAL DEFAULT 0.0,
        blocked_qty REAL DEFAULT 0.0,
        in_transit_qty REAL DEFAULT 0.0,
        UNIQUE(material_id, plant_id, warehouse_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movement_number TEXT UNIQUE NOT NULL,
        movement_type TEXT NOT NULL,  -- 101=GR Compra, 261=Consumo Prod, 601=Entrega SD
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        quantity REAL NOT NULL,
        posting_date TEXT NOT NULL,
        reference_doc TEXT,
        text TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS physical_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pi_number TEXT UNIQUE NOT NULL,
        plant_id INTEGER REFERENCES plants(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        count_date TEXT NOT NULL,
        status TEXT DEFAULT 'CREATED',  -- CREATED, COUNT_POSTED, DIFFERENCES_POSTED
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pi_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pi_id INTEGER REFERENCES physical_inventory(id),
        material_id INTEGER REFERENCES materials(id),
        book_qty REAL DEFAULT 0.0,
        counted_qty REAL,
        difference REAL DEFAULT 0.0
    )''')

    # ─────────────────────────────────────────────
    # 8. PP – PRODUCCIÓN
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS bom_headers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER REFERENCES materials(id),  -- Producto terminado
        plant_id INTEGER REFERENCES plants(id),
        base_qty REAL DEFAULT 1.0,
        status TEXT DEFAULT 'ACTIVE',
        valid_from TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bom_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_id INTEGER REFERENCES bom_headers(id),
        item_number INTEGER NOT NULL,
        component_id INTEGER REFERENCES materials(id),
        quantity REAL NOT NULL,
        unit TEXT DEFAULT 'PZA',
        item_type TEXT DEFAULT 'L'  -- L=Stock, N=Non-stock
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS work_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        plant_id INTEGER REFERENCES plants(id),
        capacity_hours_per_day REAL DEFAULT 8.0,
        cost_per_hour REAL DEFAULT 0.0,
        efficiency_pct REAL DEFAULT 100.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS routings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        operation_number INTEGER NOT NULL,
        work_center_id INTEGER REFERENCES work_centers(id),
        description TEXT,
        setup_time_min REAL DEFAULT 0.0,
        machine_time_min REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS production_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        planned_qty REAL NOT NULL,
        confirmed_qty REAL DEFAULT 0.0,
        scrap_qty REAL DEFAULT 0.0,
        planned_start TEXT,
        planned_finish TEXT,
        actual_start TEXT,
        actual_finish TEXT,
        status TEXT DEFAULT 'CREATED',  -- CREATED, RELEASED, IN_PROCESS, CONFIRMED, CLOSED
        planned_cost REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0
    )''')

    # ─────────────────────────────────────────────
    # 9. MRP – PLANIFICACIÓN
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS mrp_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TEXT NOT NULL,
        plant_id INTEGER REFERENCES plants(id),
        scope TEXT DEFAULT 'TOTAL',
        status TEXT DEFAULT 'COMPLETED',
        proposals_created INTEGER DEFAULT 0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS mrp_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrp_run_id INTEGER REFERENCES mrp_runs(id),
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        proposal_type TEXT NOT NULL,  -- PR=Purchase Req, PO=Planned Order
        quantity REAL NOT NULL,
        required_date TEXT,
        created_date TEXT,
        status TEXT DEFAULT 'OPEN'  -- OPEN, CONVERTED, CANCELLED
    )''')

    # ─────────────────────────────────────────────
    # 10. QM – GESTIÓN DE CALIDAD
    # ─────────────────────────────────────────────
    cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_number TEXT UNIQUE NOT NULL,
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        inspection_type TEXT NOT NULL,  -- 01=GR, 03=Production, 06=Customer Return
        description TEXT,
        status TEXT DEFAULT 'ACTIVE'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_characteristics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER REFERENCES inspection_plans(id),
        characteristic TEXT NOT NULL,
        lower_limit REAL,
        upper_limit REAL,
        target_value REAL,
        unit TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_number TEXT UNIQUE NOT NULL,
        plan_id INTEGER REFERENCES inspection_plans(id),
        material_id INTEGER REFERENCES materials(id),
        plant_id INTEGER REFERENCES plants(id),
        quantity REAL NOT NULL,
        origin TEXT,  -- GR, PROD, RETURN
        reference_doc TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'OPEN'  -- OPEN, INSPECTING, ACCEPTED, REJECTED
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER REFERENCES inspection_lots(id),
        characteristic_id INTEGER REFERENCES inspection_characteristics(id),
        measured_value REAL,
        result_text TEXT,
        valuation TEXT DEFAULT 'ACCEPT',  -- ACCEPT, REJECT
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    _seed_demo_data(conn)
    conn.close()
    create_initial_user()

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_initial_user():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  ("admin", hash_password("admin"), "ADMIN"))
        conn.commit()
    conn.close()

def _seed_demo_data(conn):
    """Insert demo data if tables are empty."""
    cursor = conn.cursor()

    # Companies
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO companies (code, name, country, currency) VALUES ('MX01', 'Zyra México S.A. de C.V.', 'MX', 'MXN')")
        cursor.execute("SELECT id FROM companies WHERE code='MX01'")
        comp_id = cursor.fetchone()[0]

        # Plants
        cursor.execute("INSERT INTO plants (code, name, company_id, address) VALUES ('P001', 'Planta Central CDMX', ?, 'Av. Insurgentes Sur 1234, CDMX')", (comp_id,))
        cursor.execute("INSERT INTO plants (code, name, company_id, address) VALUES ('P002', 'Planta Norte MTY', ?, 'Av. Constitución 456, MTY')", (comp_id,))
        cursor.execute("SELECT id FROM plants WHERE code='P001'")
        p1 = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM plants WHERE code='P002'")
        p2 = cursor.fetchone()[0]

        # Warehouses
        cursor.execute("INSERT INTO warehouses (code, name, plant_id) VALUES ('WH01', 'Almacén Central', ?)", (p1,))
        cursor.execute("INSERT INTO warehouses (code, name, plant_id) VALUES ('WH02', 'Almacén Producción', ?)", (p1,))
        cursor.execute("INSERT INTO warehouses (code, name, plant_id) VALUES ('WH03', 'Almacén Norte', ?)", (p2,))

        # Cost Centers
        cursor.execute("INSERT INTO cost_centers (code, name, company_id, type) VALUES ('CC-ADM', 'Administración General', ?, 'OVERHEAD')", (comp_id,))
        cursor.execute("INSERT INTO cost_centers (code, name, company_id, type) VALUES ('CC-PROD', 'Producción', ?, 'PRODUCTION')", (comp_id,))
        cursor.execute("INSERT INTO cost_centers (code, name, company_id, type) VALUES ('CC-VEN', 'Ventas', ?, 'SALES')", (comp_id,))
        cursor.execute("INSERT INTO cost_centers (code, name, company_id, type) VALUES ('CC-LOG', 'Logística', ?, 'LOGISTICS')", (comp_id,))

        # GL Accounts
        for acc in [
            ('1100', 'Caja y Bancos', 'ASSET', comp_id),
            ('1200', 'Cuentas por Cobrar', 'ASSET', comp_id),
            ('1300', 'Inventarios', 'ASSET', comp_id),
            ('1500', 'Activo Fijo', 'ASSET', comp_id),
            ('2100', 'Cuentas por Pagar', 'LIABILITY', comp_id),
            ('2200', 'IVA por Pagar', 'LIABILITY', comp_id),
            ('3100', 'Capital Social', 'EQUITY', comp_id),
            ('4100', 'Ventas', 'INCOME', comp_id),
            ('5100', 'Costo de Ventas', 'EXPENSE', comp_id),
            ('5200', 'Gastos de Operación', 'EXPENSE', comp_id),
        ]:
            cursor.execute("INSERT INTO gl_accounts (code, name, type, company_id) VALUES (?, ?, ?, ?)", acc)

        # Vendors
        for v in [
            ('V001', 'Suministros Industriales S.A.', 'MX', 30),
            ('V002', 'Tecnología de Punta Ltd.', 'MX', 45),
            ('V003', 'Import Global Corp.', 'US', 60),
        ]:
            cursor.execute("INSERT INTO vendors (code, name, country, payment_terms) VALUES (?, ?, ?, ?)", v)

        # Customers
        for c in [
            ('C001', 'Distribuidora Alfa', 'MX', 500000, 30),
            ('C002', 'Mayoreo Beta S.A.', 'MX', 200000, 45),
            ('C003', 'Comercial Gamma', 'MX', 150000, 15),
        ]:
            cursor.execute("INSERT INTO customers (code, name, country, credit_limit, payment_terms) VALUES (?, ?, ?, ?, ?)", c)

        # Materials
        cursor.execute("SELECT id FROM plants WHERE code='P001'")
        p1 = cursor.fetchone()[0]
        mats = [
            ('MAT-001', 'Engrane de Acero 12mm', 'ROH', 'PZA', 0.15),
            ('MAT-002', 'Placa de Aluminio 6061', 'ROH', 'KG', 2.50),
            ('MAT-003', 'Ensamble Motor Básico', 'HALB', 'PZA', 3.20),
            ('MAT-004', 'Motor Eléctrico 1.5HP', 'FERT', 'PZA', 5.80),
            ('MAT-005', 'Cable de Cobre 2.5mm', 'ROH', 'MT', 0.05),
        ]
        mat_ids = []
        for m in mats:
            cursor.execute("INSERT INTO materials (code, description, material_type, unit_of_measure, weight_kg) VALUES (?, ?, ?, ?, ?)", m)
            mat_ids.append(cursor.lastrowid)

        # Material Plants + Valuation + Stock
        cursor.execute("SELECT id FROM warehouses WHERE code='WH01'")
        wh1 = cursor.fetchone()[0]
        prices = [25.50, 180.00, 450.00, 2800.00, 35.00]
        for i, mid in enumerate(mat_ids):
            cursor.execute("INSERT INTO material_plants (material_id, plant_id, lead_time_days, safety_stock, reorder_point) VALUES (?, ?, ?, ?, ?)",
                           (mid, p1, [3,7,5,10,2][i], [50,20,10,5,100][i], [100,40,20,10,200][i]))
            cursor.execute("INSERT INTO material_valuation (material_id, plant_id, valuation_class, standard_price) VALUES (?, ?, ?, ?)",
                           (mid, p1, '3000', prices[i]))
            cursor.execute("INSERT INTO stock_balances (material_id, plant_id, warehouse_id, unrestricted_qty) VALUES (?, ?, ?, ?)",
                           (mid, p1, wh1, [350, 80, 45, 12, 500][i]))

        # Work Centers
        cursor.execute("INSERT INTO work_centers (code, name, plant_id, capacity_hours_per_day, cost_per_hour) VALUES ('WC-ENS', 'Ensamble Manual', ?, 8, 250.0)", (p1,))
        cursor.execute("INSERT INTO work_centers (code, name, plant_id, capacity_hours_per_day, cost_per_hour) VALUES ('WC-TEST', 'Pruebas Eléctricas', ?, 8, 300.0)", (p1,))
        cursor.execute("INSERT INTO work_centers (code, name, plant_id, capacity_hours_per_day, cost_per_hour) VALUES ('WC-PAINT', 'Pintura', ?, 6, 200.0)", (p1,))

        conn.commit()

if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
