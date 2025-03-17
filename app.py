import sys
import subprocess

# List of required packages
REQUIRED_PACKAGES = ["flask", "bcrypt", "pytz"]

def check_dependencies():
    """Check and install missing dependencies automatically."""
    missing_packages = []

    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing_packages)}")
        install = input("Would you like to install them now? (yes/no): ").strip().lower()
        if install in ["y", "yes"]:
            for package in missing_packages:
                subprocess.run([sys.executable, "-m", "pip", "install", package])
            print("\n✅ Dependencies installed! Please restart the script.")
            sys.exit(0)
        else:
            print("\n❌ Missing dependencies. Exiting...")
            sys.exit(1)

# Run dependency check before importing other modules
check_dependencies()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB_NAME = "tool_management.db"
DEFAULT_AUTO_LOGOUT_TIME = 60
DEFAULT_AUTO_SUBMIT_LENGTH = 6
TIMEZONE = pytz.timezone("America/New_York")

def get_db_connection():
    """Connect to SQLite database and enable foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ---------------- HOME PAGE ----------------
@app.route("/")
def dashboard():
    """Redirect users to RFID verification."""
    return redirect(url_for("verify_rfid"))

# ---------------- RFID VERIFICATION ----------------
@app.route("/verify_rfid", methods=["GET", "POST"])
def verify_rfid():
    """Handles RFID verification for users and admins."""
    session.clear()

    if request.method == "POST":
        user_rfid = request.form.get("rfid")

        conn = get_db_connection()
        try:
            user = conn.execute("SELECT id, name, role FROM users WHERE rfid_tag = ?", (user_rfid,)).fetchone()
        finally:
            conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            session["rfid"] = user_rfid

            if user["role"] == "admin":
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("checkout_return"))

        return "RFID not recognized. Try again.", 401

    return render_template("verify_rfid.html")

# ---------------- CHECKOUT RETURN PAGE ----------------
@app.route("/checkout_return")
def checkout_return():
    """Page where users select whether to check out or return tools."""
    if "user_id" not in session:
        return redirect(url_for("verify_rfid"))

    logout_time = DEFAULT_AUTO_LOGOUT_TIME  # Default timeout

    # Retrieve logout time from settings if stored in the database
    conn = get_db_connection()
    setting = conn.execute("SELECT value FROM settings WHERE key = 'auto_logout_time'").fetchone()
    conn.close()

    if setting:
        logout_time = int(setting["value"])

    return render_template("checkout_return.html", user_name=session["user_name"], logout_time=logout_time)


# ---------------- CHECKOUT TOOL ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Handles tool checkout."""
    if "user_id" not in session:
        return redirect(url_for("verify_rfid"))

    return render_template("checkout.html", user_name=session["user_name"])

# ---------------- RETURN TOOL ----------------
@app.route("/return_tool", methods=["GET", "POST"])
def return_tool():
    """Handles returning a tool and increasing its quantity."""
    if "user_id" not in session:
        return redirect(url_for("verify_rfid"))

    return render_template("return_tool.html", user_name=session["user_name"])

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin_panel():
    """Render the admin panel."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    conn = get_db_connection()
    try:
        users = conn.execute("SELECT id, name, rfid_tag, role FROM users").fetchall()
        tools = conn.execute("SELECT id, name, barcode, quantity, image FROM tools").fetchall()
        rooms = conn.execute("SELECT id, name FROM rooms").fetchall()
        settings = conn.execute("SELECT key, value FROM settings").fetchall()
    finally:
        conn.close()

    return render_template("admin.html", users=users, tools=tools, rooms=rooms, settings=settings)

# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["POST"])
def add_user():
    """Allows an admin to add a new user."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    name = request.form["name"]
    rfid_tag = request.form["rfid_tag"]
    role = request.form["role"]

    conn = get_db_connection()
    conn.execute("INSERT INTO users (name, rfid_tag, role) VALUES (?, ?, ?)", (name, rfid_tag, role))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- DELETE USER ----------------
@app.route("/delete_user", methods=["POST"])
def delete_user():
    """Allows an admin to delete a user."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    user_id = request.form.get("user_id")

    if user_id:
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- ADD TOOL ----------------
@app.route("/add_tool", methods=["POST"])
def add_tool():
    """Allows an admin to add a new tool."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    name = request.form["name"]
    barcode = request.form["barcode"]
    quantity = request.form["quantity"]
    image = request.form["image"]

    conn = get_db_connection()
    conn.execute("INSERT INTO tools (name, barcode, quantity, image) VALUES (?, ?, ?, ?)", 
                 (name, barcode, quantity, image))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- ADD ROOM ----------------
@app.route("/add_room", methods=["POST"])
def add_room():
    """Allows an admin to add a room for checkout tracking."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    room_name = request.form["room_name"]

    conn = get_db_connection()
    conn.execute("INSERT INTO rooms (name) VALUES (?)", (room_name,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- UPDATE ADMIN SETTINGS ----------------
@app.route("/update_settings", methods=["POST"])
def update_settings():
    """Updates admin settings like auto-logout time."""
    if "role" not in session or session["role"] != "admin":
        return "Unauthorized", 403

    logout_time = request.form.get("logout_time", type=int)
    submit_length = request.form.get("submit_length", type=int)

    conn = get_db_connection()
    conn.execute("UPDATE settings SET value=? WHERE key='auto_logout_time'", (logout_time,))
    conn.execute("UPDATE settings SET value=? WHERE key='auto_submit_length'", (submit_length,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()  # Clears the session
    return redirect(url_for('verify_rfid'))

# ---------------- LOGS PAGE ----------------
@app.route("/logs")
def logs():
    """Display transaction logs of tool checkouts and returns."""
    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    logs = conn.execute("""
        SELECT transactions.id, users.name AS user_name, tools.name AS tool_name, 
               transactions.checkout_time, transactions.return_time
        FROM transactions
        JOIN users ON transactions.user_id = users.id
        JOIN tools ON transactions.tool_id = tools.id
        ORDER BY transactions.checkout_time DESC
    """).fetchall()
    conn.close()

    return render_template("logs.html", logs=logs)

# ---------------- RUN FLASK APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
