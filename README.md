# MediFlow IMS — Pharmacy Inventory & Management System

A Python + Streamlit inventory application for managing medicine records, stock levels, expiry dates, sales and operational reporting.

## Redesigned release

This release retains the existing Streamlit application and its modules while upgrading the data layer and dashboard:

- **SQLite database** for structured medicine, sales, supplier, user and stock-movement records.
- **One-time CSV migration**: existing `data/medicines.csv`, `data/sales.csv` and `data/suppliers.csv` are imported into SQLite on first run when the corresponding database table is empty. Original CSVs are kept as import backups.
- **Transactional sales**: a sale, stock deduction and stock-movement record are committed together, preventing partial transactions.
- **Password security**: new accounts use salted PBKDF2-HMAC-SHA256 password hashes. Legacy SHA-256 account hashes are upgraded after a successful login.
- **Dashboard refresh**: KPI cards, date/category filters, sales trend, category mix, low-stock and expiry attention tables, and recent stock movements.
- **Dynamic dates**: expiry and sales views use the current system date instead of a fixed demo date.

## Features

1. Dashboard and inventory analytics
2. Add, view, search, update and delete medicine records
3. Stock adjustments and stock movement history
4. Sales checkout, invoice generation and automatic stock deduction
5. Expiry tracking and alerts
6. Reports and CSV exports
7. Account registration and sign-in

## Tech stack

- Python
- Streamlit
- SQLite
- Pandas and NumPy
- Plotly and Matplotlib

## Run locally (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` in your browser and create an account. Passwords must be at least 8 characters long.

## Database location and backup

By default the SQLite database is created at `data/mediflow.db`. It is intentionally excluded from Git because it contains account and operational records. Back it up securely; do not commit it to a public repository.

To use a different database path, set the `MEDIFLOW_DB_PATH` environment variable before starting Streamlit.

## Deploying on Streamlit Community Cloud

The app can be deployed from this repository with `app.py` as the entry point. **Important:** Streamlit Community Cloud's local filesystem is not a durable database service. A SQLite database created inside the running app may be reset when the app is rebuilt or its instance is replaced. This SQLite setup is appropriate for local demonstrations and development. Before using the hosted app for ongoing multi-user data, move the database to a managed persistent service (for example, PostgreSQL/Supabase) and configure credentials using Streamlit Secrets. Do not enter real patient, customer or confidential pharmacy data in a public demo.

## Project structure

```text
MediFlow_IMS/
├── app.py
├── requirements.txt
├── assets/
│   ├── logo.png
│   └── styles.css
├── data/                 # CSV import files; runtime SQLite DB is git-ignored
├── pages/
│   ├── Dashboard.py
│   ├── Add_Medicine.py
│   ├── View_Medicines.py
│   ├── Update_Stock.py
│   ├── Sales.py
│   ├── Expiry_Tracker.py
│   ├── Reports.py
│   └── Settings.py
└── utils/
    ├── auth.py
    ├── file_handler.py   # SQLite data access and CSV migration
    ├── analytics.py
    ├── charts.py
    ├── helper.py
    └── validations.py
```

## Important project scope

This is an academic/demo inventory application, not a validated pharmacy dispensing or clinical decision-support system. Medicine suitability, prescriptions, patient data and regulatory workflows are outside its scope.
