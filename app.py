from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB_NAME = "tool_management.db"
DEFAULT_AUTO_LOGOUT_TIME = 60  # Default to 60 seconds

TIMEZONE = pytz.timezone("America/New_York")

def get_db_connection():
    """Connect to SQLite database and enable foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Ensure foreign keys are enforced
    return conn

# ---------------- HOME PAGE: REDIRECT TO RFID VERIFICATION ----------------
@app.route("/")
def dashboard():
    """Redirect users to RFID verification."""
    return redirect(url_for("verify_rfid"))

# ---------------- RFID VERIFICATION ----------------
@app.route("/verify_rfid", methods=["GET", "POST"])
def verify_rfid():
    """Handles RFID verification for users and admins."""
    if request.method == "POST":
        user_rfid = request.form.get("rfid")

        conn = get_db_connection()
        try:
            admin = conn.execute("SELECT id, username FROM admins WHERE rfid_tag = ?", (user_rfid,)).fetchone()
            user = conn.execute("SELECT id, name, role FROM users WHERE rfid_tag = ?", (user_rfid,)).fetchone()
        finally:
            conn.close()

        if admin:
            session["admin"] = True
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("admin_panel"))

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            session["rfid"] = user_rfid
            return redirect(url_for("checkout"))

        return "RFID not recognized. Try again.", 401

    return render_template("verify_rfid.html")

# ---------------- CHECKOUT PAGE ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Tool checkout page (only accessible after RFID verification)."""
    if "user_id" not in session:
        return redirect(url_for("verify_rfid"))

    conn = get_db_connection()
    try:
        logout_time = conn.execute("SELECT value FROM settings WHERE key='auto_logout_time'").fetchone()
        logout_time = int(logout_time["value"]) if logout_time else DEFAULT_AUTO_LOGOUT_TIME
    finally:
        conn.close()

    return render_template("checkout.html", user_name=session["user_name"], user_rfid=session["rfid"], logout_time=logout_time)

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin_panel():
    """Render the admin panel (only for admins)."""
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    try:
        users = conn.execute("SELECT id, name, rfid_tag, role FROM users").fetchall()
        tools = conn.execute("SELECT id, name, barcode, quantity FROM tools").fetchall()
    finally:
        conn.close()

    return render_template("admin.html", users=users, tools=tools)

# ---------------- LOGIN PAGE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles admin login using username and password."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        finally:
            conn.close()

        if admin and bcrypt.checkpw(password.encode("utf-8"), admin["password"].encode("utf-8")):
            session["admin"] = True
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("admin_panel"))

        return "Invalid credentials", 401

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    """Logs out the user and redirects to RFID verification."""
    session.clear()
    return redirect(url_for("verify_rfid"))

# ---------------- RUN FLASK APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
