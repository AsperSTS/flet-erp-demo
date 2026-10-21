# Zyra ERP — Demo

Desktop demo of a SAP-like ERP, built with **Flet** (Python) and **SQLite**. Includes FI/CO, MM, SD, PP, QM modules, master data, a dashboard and a live simulator that generates random sales and inventory movements.

## Running

```bash
# Conda option
conda env create -f environment.yml
conda activate zyra_312_dev
python main.py

# pip option
pip install -r requirements.txt
python main.py
```

Initial credentials: **admin / admin** (you can also register or recover your password from the login screen). The database is created and seeded automatically on first launch.

## Structure

- `main.py` — startup, routing and layout
- `database.py` — SQLite schema (42 tables), seed and password hashing
- `views/` — ERP modules (dashboard, FI, CO, MM, SD, PP, QM…)
- `components/` — sidebar and base views
- `services/live_demo.py` — real-time activity simulator

## Packaging

`build.sh` bundles the app as a standalone executable with Nuitka.
