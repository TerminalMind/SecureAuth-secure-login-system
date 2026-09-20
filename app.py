import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from werkzeug.security import safe_join

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "secure_login.db")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-secret-key"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Set True behind HTTPS in production.
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

csrf = CSRFProtect(app)
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        is_locked INTEGER NOT NULL DEFAULT 0,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        lock_until TEXT,
        totp_secret TEXT,
        totp_enabled INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        last_login TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        event TEXT NOT NULL,
        ip TEXT,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def log_event(username, event):
    conn = db()
    conn.execute(
        "INSERT INTO audit_logs (username, event, ip, created_at) VALUES (?, ?, ?, ?)",
        (username, event, request.remote_addr, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

def valid_username(value):
    return 3 <= len(value) <= 30 and value.replace("_", "").isalnum()

def valid_email(value):
    return 5 <= len(value) <= 254 and "@" in value and "." in value.rsplit("@", 1)[-1]

def strong_password(value):
    return (
        len(value) >= 12
        and any(c.islower() for c in value)
        and any(c.isupper() for c in value)
        and any(c.isdigit() for c in value)
        and any(not c.isalnum() for c in value)
    )

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not valid_username(username):
            flash("Username must be 3-30 characters and contain only letters, numbers, or underscore.")
            return render_template("register.html")
        if not valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("register.html")
        if not strong_password(password):
            flash("Password must be at least 12 characters and include upper, lower, number, and special character.")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.")
            return render_template("register.html")

        try:
            password_hash = ph.hash(password)
            conn = db()
            conn.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            conn.close()
            log_event(username, "USER_REGISTERED")
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email is already registered.")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        conn = db()
        user = conn.execute(
            "SELECT * FROM users WHERE lower(username)=? OR lower(email)=?",
            (identifier, identifier),
        ).fetchone()

        if not user:
            log_event(identifier[:80], "LOGIN_FAILED")
            flash("Invalid username or password.")
            conn.close()
            return render_template("login.html")

        if user["is_locked"]:
            lock_until = user["lock_until"]
            if lock_until and datetime.fromisoformat(lock_until) > datetime.now(timezone.utc):
                flash("Account temporarily locked. Try again later.")
                conn.close()
                return render_template("login.html")
            conn.execute("UPDATE users SET is_locked=0, failed_attempts=0, lock_until=NULL WHERE id=?", (user["id"],))
            conn.commit()

        try:
            ph.verify(user["password_hash"], password)
        except (VerifyMismatchError, Exception):
            attempts = user["failed_attempts"] + 1
            if attempts >= 5:
                until = datetime.now(timezone.utc) + timedelta(minutes=10)
                conn.execute(
                    "UPDATE users SET failed_attempts=?, is_locked=1, lock_until=? WHERE id=?",
                    (attempts, until.isoformat(), user["id"]),
                )
                log_event(user["username"], "ACCOUNT_LOCKED")
            else:
                conn.execute("UPDATE users SET failed_attempts=? WHERE id=?", (attempts, user["id"]))
            conn.commit()
            conn.close()
            log_event(user["username"], "LOGIN_FAILED")
            flash("Invalid username or password.")
            return render_template("login.html")

        if user["totp_enabled"]:
            session["pending_user_id"] = user["id"]
            session["pending_2fa"] = True
            conn.close()
            return redirect(url_for("verify_2fa"))

        session.clear()
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        conn.execute(
            "UPDATE users SET failed_attempts=0, is_locked=0, lock_until=NULL, last_login=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), user["id"]),
        )
        conn.commit()
        conn.close()
        log_event(user["username"], "LOGIN_SUCCESS")
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def verify_2fa():
    if not session.get("pending_2fa"):
        return redirect(url_for("login"))
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["pending_user_id"],)).fetchone()
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if user and user["totp_secret"] and pyotp.TOTP(user["totp_secret"]).verify(code, valid_window=1):
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            conn.execute(
                "UPDATE users SET failed_attempts=0, is_locked=0, lock_until=NULL, last_login=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), user["id"]),
            )
            conn.commit()
            conn.close()
            log_event(user["username"], "2FA_SUCCESS")
            return redirect(url_for("dashboard"))
        log_event(user["username"] if user else None, "2FA_FAILED")
        flash("Invalid 2FA code.")
    conn.close()
    return render_template("verify_2fa.html")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    logs = conn.execute(
        "SELECT event, created_at FROM audit_logs WHERE username=? ORDER BY id DESC LIMIT 10",
        (session["username"],),
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", user=user, logs=logs)

@app.route("/2fa/setup", methods=["GET", "POST"])
@login_required
def setup_2fa():
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if user["totp_enabled"]:
        conn.close()
        flash("2FA is already enabled.")
        return redirect(url_for("dashboard"))

    secret = user["totp_secret"] or pyotp.random_base32()
    conn.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, user["id"]))
    conn.commit()

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if pyotp.TOTP(secret).verify(code, valid_window=1):
            conn.execute("UPDATE users SET totp_enabled=1 WHERE id=?", (user["id"],))
            conn.commit()
            conn.close()
            log_event(user["username"], "2FA_ENABLED")
            flash("2FA enabled successfully.")
            return redirect(url_for("dashboard"))
        flash("Invalid code. Try again.")

    uri = pyotp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name="SecureAuth")
    conn.close()
    return render_template("setup_2fa.html", secret=secret, uri=uri)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    username = session.get("username")

    session.clear()

    log_event(username, "LOGOUT")

    flash("You have been logged out.")

    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin():
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if not user["is_admin"]:
        conn.close()
        return "Forbidden", 403
    users = conn.execute("SELECT id, username, email, is_locked, totp_enabled, created_at, last_login FROM users ORDER BY id DESC").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("admin.html", users=users, logs=logs)

@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("Database initialized.")

init_db()

if __name__ == "__main__":
    app.run(debug=True)
