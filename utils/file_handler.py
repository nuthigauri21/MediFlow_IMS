"""CSV-backed persistence layer for MediFlow IMS.

Pandas is used to read/write structured CSV datasets. Writes are staged to a
temporary file and atomically replaced to reduce the chance of corrupt files.
"""
from __future__ import annotations
import os
import datetime as dt
import tempfile
from typing import Dict, Any
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.environ.get("MEDIFLOW_DATA_DIR", os.path.join(BASE_DIR, "data"))
MEDICINES_FILE = os.path.join(DATA_DIR, "medicines.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")
SUPPLIERS_FILE = os.path.join(DATA_DIR, "suppliers.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
MOVEMENTS_FILE = os.path.join(DATA_DIR, "stock_movements.csv")

MEDICINE_COLUMNS = ["Medicine ID", "Medicine Name", "Category", "Manufacturer", "Batch Number", "Purchase Date", "Expiry Date", "Quantity", "Unit Price", "Supplier Name"]
SALES_COLUMNS = ["Invoice Number", "Medicine ID", "Medicine Name", "Quantity Sold", "Selling Price", "Customer Name", "Sale Date", "Total Amount"]
SUPPLIER_COLUMNS = ["Supplier ID", "Supplier Name", "Contact Person", "Phone", "Email", "Address"]
MOVEMENT_COLUMNS = ["Medicine ID", "Movement", "Quantity Change", "Quantity After", "Note", "Date"]
USER_COLUMNS = ["Username", "PasswordHash", "Email", "SignupDate"]


def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)


def _read(path: str, columns: list[str]) -> pd.DataFrame:
    ensure_directories()
    if not os.path.exists(path):
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(path).reindex(columns=columns)
    except (pd.errors.EmptyDataError, UnicodeDecodeError):
        return pd.DataFrame(columns=columns)


def _write(path: str, df: pd.DataFrame, columns: list[str]) -> bool:
    ensure_directories()
    try:
        clean = df.reindex(columns=columns).copy()
        fd, temp_path = tempfile.mkstemp(prefix=".mediflow_", suffix=".csv", dir=DATA_DIR)
        os.close(fd)
        clean.to_csv(temp_path, index=False)
        os.replace(temp_path, path)
        return True
    except Exception as exc:
        print(f"CSV write failed for {os.path.basename(path)}: {exc}")
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path): os.remove(temp_path)
        except OSError:
            pass
        return False


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("Quantity", "Quantity Sold", "Quantity Change", "Quantity After"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("Unit Price", "Selling Price", "Total Amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def init_files(reset: bool = False):
    """Ensure all application CSV files exist; never overwrite existing records."""
    ensure_directories()
    schemas = [(MEDICINES_FILE, MEDICINE_COLUMNS), (SALES_FILE, SALES_COLUMNS),
               (SUPPLIERS_FILE, SUPPLIER_COLUMNS), (USERS_FILE, USER_COLUMNS),
               (MOVEMENTS_FILE, MOVEMENT_COLUMNS)]
    for path, columns in schemas:
        if reset and path in (MEDICINES_FILE, SALES_FILE, MOVEMENTS_FILE):
            _write(path, pd.DataFrame(columns=columns), columns)
        elif not os.path.exists(path):
            _write(path, pd.DataFrame(columns=columns), columns)


def load_medicines():
    init_files(); return _normalize(_read(MEDICINES_FILE, MEDICINE_COLUMNS))

def save_medicines(df): return _write(MEDICINES_FILE, df, MEDICINE_COLUMNS)

def load_sales():
    init_files(); return _normalize(_read(SALES_FILE, SALES_COLUMNS))

def save_sales(df): return _write(SALES_FILE, df, SALES_COLUMNS)

def load_suppliers():
    init_files(); return _read(SUPPLIERS_FILE, SUPPLIER_COLUMNS)

def save_suppliers(df): return _write(SUPPLIERS_FILE, df, SUPPLIER_COLUMNS)

def _append_movement(med_id: str, movement: str, change: int, after: int, note: str):
    df = _read(MOVEMENTS_FILE, MOVEMENT_COLUMNS)
    row = {"Medicine ID": med_id, "Movement": movement, "Quantity Change": int(change),
           "Quantity After": int(after), "Note": note,
           "Date": dt.datetime.now().isoformat(timespec="seconds")}
    return _write(MOVEMENTS_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True), MOVEMENT_COLUMNS)


def add_medicine(data: Dict[str, Any]) -> bool:
    init_files(); df = load_medicines()
    med_id = str(data.get("Medicine ID", "")).strip()
    if not med_id or (not df.empty and df["Medicine ID"].astype(str).str.casefold().eq(med_id.casefold()).any()): return False
    row = {c: data.get(c, "") for c in MEDICINE_COLUMNS}
    row["Medicine ID"] = med_id
    try:
        row["Quantity"] = int(row["Quantity"] or 0); row["Unit Price"] = float(row["Unit Price"] or 0)
        if row["Quantity"] < 0 or row["Unit Price"] < 0: return False
    except (TypeError, ValueError): return False
    if not save_medicines(pd.concat([df, pd.DataFrame([row])], ignore_index=True)): return False
    _append_movement(med_id, "OPENING", row["Quantity"], row["Quantity"], "Initial inventory")
    return True


def update_medicine(med_id: str, data: Dict[str, Any]) -> bool:
    df = load_medicines(); mask = df["Medicine ID"].astype(str).eq(str(med_id))
    if not mask.any(): return False
    old_qty = int(df.loc[mask, "Quantity"].iloc[0])
    for key, value in data.items():
        if key in MEDICINE_COLUMNS and key != "Medicine ID": df.loc[mask, key] = value
    try:
        if int(df.loc[mask, "Quantity"].iloc[0]) < 0 or float(df.loc[mask, "Unit Price"].iloc[0]) < 0: return False
    except (TypeError, ValueError): return False
    new_qty = int(df.loc[mask, "Quantity"].iloc[0])
    ok = save_medicines(df)
    if ok and new_qty != old_qty: _append_movement(med_id, "EDIT", new_qty-old_qty, new_qty, "Medicine record updated")
    return ok


def delete_medicine(med_id: str) -> bool:
    df = load_medicines(); updated = df[df["Medicine ID"].astype(str) != str(med_id)]
    if len(updated) == len(df): return False
    return save_medicines(updated)


def update_stock(med_id: str, qty_change: int, set_absolute: bool = False) -> bool:
    df = load_medicines(); mask = df["Medicine ID"].astype(str).eq(str(med_id))
    if not mask.any(): return False
    old = int(df.loc[mask, "Quantity"].iloc[0]); new = int(qty_change) if set_absolute else old + int(qty_change)
    if new < 0: return False
    df.loc[mask, "Quantity"] = new
    if not save_medicines(df): return False
    delta = new - old
    if delta: _append_movement(med_id, "ADJUSTMENT", delta, new, "Manual stock adjustment")
    return True


def record_sale(sale_data: Dict[str, Any]) -> bool:
    init_files(); meds = load_medicines(); sales = load_sales()
    med_id = str(sale_data.get("Medicine ID", "")); mask = meds["Medicine ID"].astype(str).eq(med_id)
    if not mask.any(): return False
    qty = int(sale_data.get("Quantity Sold", 0)); old_qty = int(meds.loc[mask, "Quantity"].iloc[0])
    if qty <= 0 or old_qty < qty: return False
    invoice = str(sale_data.get("Invoice Number", ""))
    if not invoice or (not sales.empty and sales["Invoice Number"].astype(str).eq(invoice).any()): return False
    med_name = str(meds.loc[mask, "Medicine Name"].iloc[0])
    row = {c: sale_data.get(c, "") for c in SALES_COLUMNS}
    row.update({"Medicine ID": med_id, "Medicine Name": sale_data.get("Medicine Name", med_name),
                "Quantity Sold": qty, "Selling Price": float(sale_data["Selling Price"]),
                "Total Amount": float(sale_data["Total Amount"])})
    meds.loc[mask, "Quantity"] = old_qty - qty
    # Stage both datasets; roll back the first file if the second write fails.
    old_meds = meds.copy(); old_meds.loc[mask, "Quantity"] = old_qty
    if not save_medicines(meds): return False
    if not save_sales(pd.concat([sales, pd.DataFrame([row])], ignore_index=True)):
        save_medicines(old_meds); return False
    _append_movement(med_id, "SALE", -qty, old_qty-qty, f"Invoice {invoice}")
    return True


def load_stock_movements(limit: int = 100) -> pd.DataFrame:
    init_files(); df = _read(MOVEMENTS_FILE, MOVEMENT_COLUMNS)
    return _normalize(df).tail(int(limit)).iloc[::-1].reset_index(drop=True)


def reset_database() -> bool:
    init_files(reset=True); return True
