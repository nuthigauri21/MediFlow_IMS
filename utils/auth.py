"""SQLite-backed account registration and authentication."""
import hashlib, hmac, os, datetime
from typing import Tuple
from utils.file_handler import get_connection, init_files

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
        # Backward compatibility for legacy SHA-256 accounts; successful login upgrades hash.
        return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), stored)
    except Exception:
        return False

def register_user(username: str, password: str, email: str) -> Tuple[bool, str]:
    username, email = username.strip(), email.strip().lower()
    if not username or not password or not email: return False, "All fields are required."
    if len(username) < 3: return False, "Username must contain at least 3 characters."
    if len(password) < 8: return False, "Use a password with at least 8 characters."
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]: return False, "Enter a valid email address."
    init_files()
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO users(username,password_hash,email,signup_date) VALUES(?,?,?,?)", (username, _hash_password(password), email, datetime.datetime.now().isoformat(timespec="seconds")))
        return True, "Account created successfully. You can now sign in."
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc): return False, "That username is already registered. Please sign in instead."
        return False, "Could not create the account. Please try again."

def authenticate_user(username: str, password: str) -> bool:
    if not username.strip() or not password: return False
    init_files()
    with get_connection() as conn:
        row = conn.execute("SELECT username,password_hash FROM users WHERE username=? COLLATE NOCASE", (username.strip(),)).fetchone()
        if not row or not _verify_password(password, row["password_hash"]): return False
        if not row["password_hash"].startswith("pbkdf2_sha256$"):
            conn.execute("UPDATE users SET password_hash=? WHERE username=?", (_hash_password(password), row["username"]))
        return True
