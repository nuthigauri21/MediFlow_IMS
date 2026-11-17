"""SQLite-backed data layer for MediFlow IMS.

The existing CSV files are imported once into SQLite on first startup. Public
function names and DataFrame column names remain compatible with existing pages.
"""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
import datetime as dt
from typing import Dict, Any
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.environ.get("MEDIFLOW_DB_PATH", os.path.join(DATA_DIR, "mediflow.db"))
MEDICINES_FILE = os.path.join(DATA_DIR, "medicines.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")
SUPPLIERS_FILE = os.path.join(DATA_DIR, "suppliers.csv")

MEDICINE_COLUMNS = ["Medicine ID", "Medicine Name", "Category", "Manufacturer", "Batch Number", "Purchase Date", "Expiry Date", "Quantity", "Unit Price", "Supplier Name"]
SALES_COLUMNS = ["Invoice Number", "Medicine ID", "Medicine Name", "Quantity Sold", "Selling Price", "Customer Name", "Sale Date", "Total Amount"]
SUPPLIER_COLUMNS = ["Supplier ID", "Supplier Name", "Contact Person", "Phone", "Email", "Address"]


def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_connection():
    """Yield a configured connection and always close it after the operation."""
    ensure_directories()
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _table_empty(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def init_files(reset: bool = False):
    """Create schema and import existing CSV data once; never overwrite live data."""
    ensure_directories()
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id TEXT PRIMARY KEY, medicine_name TEXT NOT NULL, category TEXT,
            manufacturer TEXT, batch_number TEXT, purchase_date TEXT, expiry_date TEXT,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            unit_price REAL NOT NULL DEFAULT 0 CHECK(unit_price >= 0), supplier_name TEXT
        );
        CREATE TABLE IF NOT EXISTS sales (
            invoice_number TEXT PRIMARY KEY, medicine_id TEXT, medicine_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL CHECK(quantity_sold > 0), selling_price REAL NOT NULL,
            customer_name TEXT, sale_date TEXT NOT NULL, total_amount REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY, supplier_name TEXT NOT NULL, contact_person TEXT,
            phone TEXT, email TEXT, address TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY COLLATE NOCASE, password_hash TEXT NOT NULL,
            email TEXT NOT NULL, signup_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_id TEXT NOT NULL,
            movement_type TEXT NOT NULL, quantity_change INTEGER NOT NULL,
            quantity_after INTEGER NOT NULL, note TEXT, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_medicines_expiry ON medicines(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_medicines_category ON medicines(category);
        CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
        """)
        if reset:
            for table in ("medicines", "sales", "suppliers", "stock_movements"):
                conn.execute(f"DELETE FROM {table}")
        # One-time legacy CSV migration. CSVs remain untouched as a backup.
        imports = [("medicines", MEDICINES_FILE, MEDICINE_COLUMNS), ("sales", SALES_FILE, SALES_COLUMNS), ("suppliers", SUPPLIERS_FILE, SUPPLIER_COLUMNS)]
        for table, path, columns in imports:
            if _table_empty(conn, table) and os.path.exists(path):
                try:
                    df = pd.read_csv(path).reindex(columns=columns)
                    if not df.empty:
                        _write_frame(conn, table, df)
                except Exception as exc:
                    print(f"Legacy import skipped for {table}: {exc}")
        # Migrate legacy local account files without exposing them in the repository.
        if _table_empty(conn, "users"):
            legacy_users = os.path.join(DATA_DIR, "users.csv")
            legacy_excel = os.path.join(DATA_DIR, "users.xlsx")
            old_users = None
            try:
                if os.path.exists(legacy_users): old_users = pd.read_csv(legacy_users)
                elif os.path.exists(legacy_excel): old_users = pd.read_excel(legacy_excel)
            except Exception as exc:
                print(f"Legacy user migration skipped: {exc}")
            if old_users is not None and not old_users.empty:
                for _, user in old_users.iterrows():
                    if all(k in old_users.columns for k in ("Username", "PasswordHash", "Email", "SignupDate")):
                        conn.execute("INSERT OR IGNORE INTO users(username,password_hash,email,signup_date) VALUES(?,?,?,?)", (str(user["Username"]), str(user["PasswordHash"]), str(user["Email"]), str(user["SignupDate"])))


def _write_frame(conn, table: str, df: pd.DataFrame):
    mapping = {
        "medicines": dict(zip(MEDICINE_COLUMNS, ["medicine_id", "medicine_name", "category", "manufacturer", "batch_number", "purchase_date", "expiry_date", "quantity", "unit_price", "supplier_name"])),
        "sales": dict(zip(SALES_COLUMNS, ["invoice_number", "medicine_id", "medicine_name", "quantity_sold", "selling_price", "customer_name", "sale_date", "total_amount"])),
        "suppliers": dict(zip(SUPPLIER_COLUMNS, ["supplier_id", "supplier_name", "contact_person", "phone", "email", "address"])),
    }
    clean = df.copy().rename(columns=mapping[table])
    clean = clean.where(pd.notna(clean), None)
    clean.to_sql(table, conn, if_exists="append", index=False)


def _load(table: str, columns: list[str]) -> pd.DataFrame:
    init_files()
    with get_connection() as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    reverse = {
        "medicines": dict(zip(["medicine_id", "medicine_name", "category", "manufacturer", "batch_number", "purchase_date", "expiry_date", "quantity", "unit_price", "supplier_name"], MEDICINE_COLUMNS)),
        "sales": dict(zip(["invoice_number", "medicine_id", "medicine_name", "quantity_sold", "selling_price", "customer_name", "sale_date", "total_amount"], SALES_COLUMNS)),
        "suppliers": dict(zip(["supplier_id", "supplier_name", "contact_person", "phone", "email", "address"], SUPPLIER_COLUMNS)),
    }
    if df.empty:
        return pd.DataFrame(columns=columns)
    df = df.rename(columns=reverse[table]).reindex(columns=columns)
    for col in ("Quantity", "Quantity Sold"):
        if col in df: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("Unit Price", "Selling Price", "Total Amount"):
        if col in df: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def _save(table: str, df: pd.DataFrame, columns: list[str], key_col: str) -> bool:
    try:
        init_files()
        with get_connection() as conn:
            conn.execute(f"DELETE FROM {table}")
            if not df.empty: _write_frame(conn, table, df.reindex(columns=columns))
        return True
    except Exception as exc:
        print(f"Database save failed for {table}: {exc}")
        return False


def load_medicines(): return _load("medicines", MEDICINE_COLUMNS)
def save_medicines(df): return _save("medicines", df, MEDICINE_COLUMNS, "Medicine ID")
def load_sales(): return _load("sales", SALES_COLUMNS)
def save_sales(df): return _save("sales", df, SALES_COLUMNS, "Invoice Number")
def load_suppliers(): return _load("suppliers", SUPPLIER_COLUMNS)
def save_suppliers(df): return _save("suppliers", df, SUPPLIER_COLUMNS, "Supplier ID")


def add_medicine(data: Dict[str, Any]) -> bool:
    init_files()
    try:
        row = {"Medicine ID": data.get("Medicine ID"), **data}
        with get_connection() as conn:
            conn.execute("INSERT INTO medicines VALUES (?,?,?,?,?,?,?,?,?,?)", tuple(row.get(c) for c in ["Medicine ID", "Medicine Name", "Category", "Manufacturer", "Batch Number", "Purchase Date", "Expiry Date", "Quantity", "Unit Price", "Supplier Name"]))
            conn.execute("INSERT INTO stock_movements(medicine_id,movement_type,quantity_change,quantity_after,note,created_at) VALUES(?,?,?,?,?,?)", (row["Medicine ID"], "OPENING", int(row.get("Quantity",0)), int(row.get("Quantity",0)), "Initial inventory", dt.datetime.now().isoformat(timespec="seconds")))
        return True
    except Exception as exc:
        print(f"Add medicine failed: {exc}"); return False


def update_medicine(med_id: str, data: Dict[str, Any]) -> bool:
    init_files()
    allowed = {"Medicine Name":"medicine_name", "Category":"category", "Manufacturer":"manufacturer", "Batch Number":"batch_number", "Purchase Date":"purchase_date", "Expiry Date":"expiry_date", "Quantity":"quantity", "Unit Price":"unit_price", "Supplier Name":"supplier_name"}
    fields = [(allowed[k], v) for k,v in data.items() if k in allowed]
    if not fields: return False
    try:
        with get_connection() as conn:
            cur = conn.execute("UPDATE medicines SET " + ",".join(f"{k}=?" for k,_ in fields) + " WHERE medicine_id=?", [v for _,v in fields]+[med_id])
            return cur.rowcount > 0
    except Exception as exc:
        print(f"Update medicine failed: {exc}"); return False


def delete_medicine(med_id: str) -> bool:
    init_files()
    try:
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM medicines WHERE medicine_id=?", (med_id,))
            return cur.rowcount > 0
    except Exception as exc:
        print(f"Delete medicine failed: {exc}"); return False


def update_stock(med_id: str, qty_change: int, set_absolute: bool = False) -> bool:
    init_files()
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT quantity FROM medicines WHERE medicine_id=?", (med_id,)).fetchone()
            if not row: return False
            old = int(row["quantity"]); new = int(qty_change) if set_absolute else old + int(qty_change)
            if new < 0: return False
            conn.execute("UPDATE medicines SET quantity=? WHERE medicine_id=?", (new, med_id))
            delta = new-old
            if delta:
                conn.execute("INSERT INTO stock_movements(medicine_id,movement_type,quantity_change,quantity_after,note,created_at) VALUES(?,?,?,?,?,?)", (med_id, "ADJUSTMENT", delta, new, "Manual stock adjustment", dt.datetime.now().isoformat(timespec="seconds")))
        return True
    except Exception as exc:
        print(f"Stock update failed: {exc}"); return False


def record_sale(sale_data: Dict[str, Any]) -> bool:
    init_files()
    try:
        with get_connection() as conn:
            med = conn.execute("SELECT medicine_name, quantity FROM medicines WHERE medicine_id=?", (sale_data["Medicine ID"],)).fetchone()
            if not med or int(med["quantity"]) < int(sale_data["Quantity Sold"]): return False
            conn.execute("INSERT INTO sales VALUES(?,?,?,?,?,?,?,?)", (sale_data["Invoice Number"], sale_data["Medicine ID"], sale_data.get("Medicine Name", med["medicine_name"]), int(sale_data["Quantity Sold"]), float(sale_data["Selling Price"]), sale_data.get("Customer Name", "Walk-in Customer"), sale_data["Sale Date"], float(sale_data["Total Amount"])))
            new_qty = int(med["quantity"]) - int(sale_data["Quantity Sold"])
            conn.execute("UPDATE medicines SET quantity=? WHERE medicine_id=?", (new_qty, sale_data["Medicine ID"]))
            conn.execute("INSERT INTO stock_movements(medicine_id,movement_type,quantity_change,quantity_after,note,created_at) VALUES(?,?,?,?,?,?)", (sale_data["Medicine ID"], "SALE", -int(sale_data["Quantity Sold"]), new_qty, f"Invoice {sale_data['Invoice Number']}", dt.datetime.now().isoformat(timespec="seconds")))
        return True
    except Exception as exc:
        print(f"Sale transaction failed: {exc}"); return False


def load_stock_movements(limit: int = 100) -> pd.DataFrame:
    init_files()
    with get_connection() as conn:
        return pd.read_sql_query("SELECT medicine_id AS 'Medicine ID', movement_type AS 'Movement', quantity_change AS 'Quantity Change', quantity_after AS 'Quantity After', note AS 'Note', created_at AS 'Date' FROM stock_movements ORDER BY id DESC LIMIT ?", conn, params=(limit,))


def reset_database() -> bool:
    init_files(reset=True)
    return True
