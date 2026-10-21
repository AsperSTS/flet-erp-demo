# Zyra ERP — Demo

Demostración de escritorio de un ERP tipo SAP, construida con **Flet** (Python) y **SQLite**. Incluye módulos FI/CO, MM, SD, PP, QM, datos maestros, panel de control y un simulador en vivo que genera ventas y movimientos de inventario aleatorios.

## Ejecución

```bash
# Opción conda
conda env create -f environment.yml
conda activate zyra_312_dev
python main.py

# Opción pip
pip install -r requirements.txt
python main.py
```

Credenciales iniciales: **admin / admin** (también puede registrarse o recuperar contraseña desde el login). La base de datos se crea y alimenta automáticamente al primer arranque.

## Estructura

- `main.py` — arranque, enrutado y layout
- `database.py` — esquema SQLite (42 tablas), seed y hashing de contraseñas
- `views/` — módulos ERP (dashboard, FI, CO, MM, SD, PP, QM…)
- `components/` — barra lateral y vistas base
- `services/live_demo.py` — simulador de actividad en tiempo real

## Compilación

`build.sh` empaqueta la app como standalone con Nuitka.
