import sqlite3
import bcrypt

DB_NAME = "tool_management.db"

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def login_admin(username, password):
    """Handle admin login."""
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()

    if not admin:
        # If no admin exists, create a default one
        default_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
        conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", default_password))
        conn.commit()
        conn.close()
        return {"error": "Default admin created. Please log in with 'admin' / 'admin123'"}

    if bcrypt.checkpw(password.encode("utf-8"), admin["password"]):
        admin_data = {"id": admin["id"], "username": admin["username"]}
        conn.close()
        return {"message": "Login successful", "admin": admin_data}
    else:
        conn.close()
        return {"error": "Invalid credentials"}

def logout_admin():
    """Log out the admin."""
    return {"message": "Logged out successfully"}

def change_admin_password(admin_id, new_password):
    """Change an admin’s password."""
    if not new_password or len(new_password) < 6:
        return {"error": "Password must be at least 6 characters long"}

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    conn = get_db_connection()
    conn.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed_password, admin_id))
    conn.commit()
    conn.close()

    return {"message": "Password updated successfully"}
