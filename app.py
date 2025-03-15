from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import pytz  # Install this with: pip install pytz

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB_NAME = "tool_management.db"
DEFAULT_AUTO_LOGOUT_TIME = 60  # Default to 60 seconds

TIMEZONE = pytz.timezone("America/New_York")  # Change to your timezone


def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME PAGE: REDIRECT TO RFID VERIFICATION ----------------
@app.route("/")
def dashboard():
    """Redirect users to RFID verification first."""
    return redirect(url_for("verify_rfid"))


# ---------------- RFID VERIFICATION ----------------
@app.route("/verify_rfid", methods=["GET", "POST"])
def verify_rfid():
    """RFID verification page before allowing tool checkout."""
    if request.method == "POST":
        user_rfid = request.form.get("rfid")

        conn = get_db_connection()
        user = conn.execute("SELECT id, name FROM users WHERE rfid_tag = ?", (user_rfid,)).fetchone()
        conn.close()

        if not user:
            return "RFID not recognized. Try again.", 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["rfid"] = user_rfid

        return redirect(url_for("checkout"))

    return render_template("verify_rfid.html")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Tool checkout page (only accessible after RFID verification)."""
    if "user_id" not in session:
        return redirect(url_for("verify_rfid"))

    conn = get_db_connection()
    logout_time = conn.execute("SELECT value FROM settings WHERE key='auto_logout_time'").fetchone()
    logout_time = int(logout_time["value"]) if logout_time else DEFAULT_AUTO_LOGOUT_TIME
    conn.close()

    return render_template("checkout.html", user_name=session["user_name"], user_rfid=session["rfid"], logout_time=logout_time)


# ---------------- TOOL CHECKOUT ----------------
@app.route("/scan_tool", methods=["POST"])
def scan_tool():
    """Handles tool checkout using RFID and barcode scanning."""
    if "user_id" not in session:
        return jsonify({"error": "RFID verification required!"}), 403

    data = request.get_json()
    tool_barcode = data.get("barcode")
    user_id = session["user_id"]

    conn = get_db_connection()
    tool = conn.execute("SELECT id, quantity FROM tools WHERE barcode = ?", (tool_barcode,)).fetchone()
    if not tool or tool["quantity"] <= 0:
        return jsonify({"error": "Tool out of stock"}), 400

    conn.execute("INSERT INTO transactions (user_id, tool_id, checkout_time) VALUES (?, ?, datetime('now'))", (user_id, tool["id"]))
    conn.execute("UPDATE tools SET quantity = quantity - 1 WHERE id = ?", (tool["id"],))
    conn.commit()
    conn.close()

    return jsonify({"message": "Tool checked out successfully!"})


# ---------------- RETURN TOOL ----------------
@app.route("/return_tool", methods=["POST"])
def return_tool():
    """Handles returning a tool and increasing its quantity."""
    if "user_id" not in session:
        return jsonify({"error": "RFID verification required!"}), 403

    data = request.get_json()
    tool_barcode = data.get("barcode")
    user_id = session["user_id"]

    conn = get_db_connection()
    tool = conn.execute("SELECT id FROM tools WHERE barcode = ?", (tool_barcode,)).fetchone()
    if not tool:
        return jsonify({"error": "Tool not found"}), 404

    conn.execute("UPDATE transactions SET return_time = datetime('now') WHERE user_id = ? AND tool_id = ? AND return_time IS NULL", (user_id, tool["id"]))
    conn.execute("UPDATE tools SET quantity = quantity + 1 WHERE id = ?", (tool["id"],))
    conn.commit()
    conn.close()

    return jsonify({"message": "Tool returned successfully!"})


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin_panel():
    """Render the admin panel."""
    if not session.get("admin"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    users = conn.execute("SELECT id, name, rfid_tag FROM users").fetchall()
    tools = conn.execute("SELECT id, name, barcode, quantity FROM tools").fetchall()
    logout_time = conn.execute("SELECT value FROM settings WHERE key='auto_logout_time'").fetchone()
    logout_time = int(logout_time["value"]) if logout_time else DEFAULT_AUTO_LOGOUT_TIME
    conn.close()

    return render_template("admin.html", users=users, tools=tools, logout_time=logout_time)


# ---------------- ADD USER ----------------
@app.route("/add_user_route", methods=["POST"])
def add_user_route():
    """Allows an admin to add a new user with an RFID tag."""
    if not session.get("admin"):
        return "Unauthorized", 403

    name = request.form.get("name")
    rfid_tag = request.form.get("rfid_tag")

    if not name or not rfid_tag:
        return "Error: Missing user name or RFID tag", 400

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (name, rfid_tag) VALUES (?, ?)", (name, rfid_tag))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Error: RFID tag already exists", 400
    finally:
        conn.close()

    return redirect(url_for("admin_panel"))

# ---------------- ADD TOOL ----------------
@app.route("/add_tool_route", methods=["POST"])
def add_tool_route():
    """Allows an admin to add a new tool with a barcode and quantity."""
    if not session.get("admin"):
        return "Unauthorized", 403

    name = request.form.get("name")
    barcode = request.form.get("barcode")
    quantity = request.form.get("quantity", type=int)

    if not name or not barcode or quantity is None or quantity < 1:
        return "Error: Missing or invalid tool data", 400

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO tools (name, barcode, quantity) VALUES (?, ?, ?)", (name, barcode, quantity))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Error: Barcode already exists", 400
    finally:
        conn.close()

    return redirect(url_for("admin_panel"))



# ---------------- DELETE USER ----------------
@app.route("/delete_user_route", methods=["POST"])
def delete_user_route():
    """Allows an admin to delete a user."""
    if not session.get("admin"):
        return "Unauthorized", 403

    user_id = request.form.get("user_id")

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))


# ---------------- DELETE TOOL ----------------
@app.route("/delete_tool_route", methods=["POST"])
def delete_tool_route():
    """Allows an admin to delete a tool."""
    if not session.get("admin"):
        return "Unauthorized", 403

    tool_id = request.form.get("tool_id")

    conn = get_db_connection()
    conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))


# ---------------- UPDATE LOGOUT TIME ----------------
@app.route("/update_logout_time_route", methods=["POST"])
def update_logout_time_route():
    """Updates the auto-logout time in the database."""
    if not session.get("admin"):
        return "Unauthorized", 403

    logout_time = request.form.get("logout_time", type=int)

    if not logout_time or logout_time < 10:
        return "Error: Auto-logout time must be at least 10 seconds", 400

    conn = get_db_connection()
    conn.execute("INSERT INTO settings (key, value) VALUES ('auto_logout_time', ?) ON CONFLICT(key) DO UPDATE SET value=?", (logout_time, logout_time))
    conn.commit()
    conn.close()

    return jsonify({"message": "Auto-logout time updated successfully!"})


# ---------------- USER LOGOUT ----------------
@app.route("/user_logout")
def user_logout():
    """Logs out the user and redirects to RFID verification."""
    session.clear()
    return redirect(url_for("verify_rfid"))

# ---------------- LOGS ----------------
@app.route("/logs")
def logs():
    """Display transaction logs of tool checkouts and returns."""
    if not session.get("admin"):
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
