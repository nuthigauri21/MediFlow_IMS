"""CSV-backed account registration and authentication."""
import hashlib, hmac, os, datetime
from typing import Tuple
import pandas as pd
from utils.file_handler import init_files, USERS_FILE, USER_COLUMNS, _read, _write

ITERATIONS = 310_000

def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        if stored.startswith("pbkdf2_sha256$"):
            _, rounds, salt_hex, digest_hex = stored.split("$")
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
            return hmac.compare_digest(actual, digest_hex)
        return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), stored)
    except Exception:
        return False

def register_user(username: str, password: str, email: str) -> Tuple[bool, str]:
    username, email = username.strip(), email.strip().lower()
    if not username or not password or not email: return False, "All fields are required."
    if len(username) < 3: return False, "Username must contain at least 3 characters."
    if len(password) < 8: return False, "Use a password with at least 8 characters."
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]: return False, "Enter a valid email address."
    init_files(); users = _read(USERS_FILE, USER_COLUMNS)
    if not users.empty and users["Username"].astype(str).str.casefold().eq(username.casefold()).any():
        return False, "That username is already registered. Please sign in instead."
    row = {"Username": username, "PasswordHash": _hash_password(password), "Email": email,
           "SignupDate": datetime.datetime.now().isoformat(timespec="seconds")}
    if _write(USERS_FILE, pd.concat([users, pd.DataFrame([row])], ignore_index=True), USER_COLUMNS):
        return True, "Account created successfully. You can now sign in."
    return False, "Could not create the account. Please try again."

def authenticate_user(username: str, password: str) -> bool:
    if not username.strip() or not password: return False
    init_files(); users = _read(USERS_FILE, USER_COLUMNS)
    if users.empty: return False
    matches = users["Username"].astype(str).str.casefold().eq(username.strip().casefold())
    if not matches.any(): return False
    idx = users.index[matches][0]; stored = str(users.loc[idx, "PasswordHash"])
    if not _verify_password(password, stored): return False
    if not stored.startswith("pbkdf2_sha256$"):
        users.loc[idx, "PasswordHash"] = _hash_password(password)
        _write(USERS_FILE, users, USER_COLUMNS)
    return True
