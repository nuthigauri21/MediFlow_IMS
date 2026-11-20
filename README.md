# MediFlow IMS — Medicine Inventory Management

MediFlow IMS is a Python-based medicine inventory management application built with Streamlit. It helps maintain medicine records, monitor stock quantities and expiry dates, record sales, and generate inventory reports.

## Features

- **Medicine records (CRUD):** add, view, search, edit/update and delete medicine records.
- **CSV-based storage:** medicine, sales, supplier, user and stock-movement records are stored as CSV files under `data/`; Pandas is used to read, validate, transform and write tabular data.
- **Stock monitoring:** manual stock adjustments, low-stock identification and a recent stock movement log.
- **Expiry tracking:** identify expired medicines and medicines approaching their expiry date.
- **Dashboard analytics:** inventory KPIs, category distribution, sales/revenue trend, low-stock and expiry attention tables.
- **Sales & invoicing:** record sales, calculate invoice totals and automatically reduce available stock.
- **Reports:** preview and download inventory, low-stock, expiry, sales and category reports as CSV. Category stock reports include a Matplotlib visualization.
- **Interactive visualizations:** Plotly charts for dashboard inventory and sales analysis.
- **Account access:** account registration and sign-in with salted PBKDF2-SHA256 password hashes. Password hashes are stored in the local `users.csv` file, not as plain text.
- **Responsive interface:** organized Streamlit navigation and dark/light theme support.

## Technology stack

- Python 3.10+
- Streamlit
- Pandas
- Matplotlib
- Plotly
- CSV file storage

## Project structure

```text
MediFlow_IMS/
├── app.py
├── requirements.txt
├── README.md
├── commands.txt
├── assets/
│   ├── logo.png
│   └── styles.css
├── data/
│   ├── medicines.csv
│   ├── sales.csv
│   ├── suppliers.csv
│   ├── users.csv                 # generated locally; ignored by Git
│   └── stock_movements.csv       # generated locally; ignored by Git
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
    ├── file_handler.py
    ├── analytics.py
    ├── charts.py
    ├── helper.py
    └── validations.py
```

## Run locally (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`, choose **Create Account**, register, and then sign in. Passwords must contain at least 8 characters.

## CSV data files

The app creates `users.csv` and `stock_movements.csv` on first launch. The supplied medicine, sales and supplier CSV files provide demonstration data. You can back up the `data` folder to preserve local records. Do not commit `users.csv` or real business/customer information to a public repository.

CSV files are suitable for a lightweight academic demonstration and single-user/local workflows. They do not provide database transactions or safe concurrent multi-user writes. For production use, migrate operational data to a managed database and add role-based access, audit controls and backups. Streamlit Community Cloud's local filesystem may be reset when an app is rebuilt or its instance is replaced; therefore, this demo should not be used as a durable production data store. Do not enter real patient or confidential pharmacy information.

## Deployment on Streamlit Community Cloud

1. Push the complete project folder to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Select branch `main` and entry point `app.py`.
4. Deploy. The dependencies are installed from `requirements.txt`.
5. Open the deployed app and create a new account.

If the hosted app is restarted or rebuilt, local CSV data may not persist. Use a managed persistent database/storage service for real deployment.

## Resume alignment

This implementation demonstrates the project scope described in the resume: Python and Streamlit application development, CSV-based CRUD operations, stock and expiry tracking, and inventory visualizations/reports using Pandas, Matplotlib and Plotly.

## Scope note

This is an academic/demo inventory management project, not a validated pharmacy dispensing or clinical decision-support system. It does not make clinical recommendations or validate prescriptions.
