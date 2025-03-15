import sqlite3

DB_NAME = "tool_management.db"

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_users():
    """Fetch all users from the database."""
    conn = get_db_connection()
    users = conn.execute("SELECT id, name, rfid_tag FROM users").fetchall()
    conn.close()
    return users

def get_tools():
    """Fetch all tools from the database."""
    conn = get_db_connection()
    tools = conn.execute("SELECT id, name, barcode, quantity FROM tools").fetchall()
    conn.close()
    return tools

def add_user(name, rfid_tag):
    """Add a new user with RFID tag."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (name, rfid_tag) VALUES (?, ?)", (name, rfid_tag))
        conn.commit()
        return {"message": "User added successfully"}
    except sqlite3.IntegrityError:
        return {"error": "RFID tag already exists"}
    finally:
        conn.close()

def add_tool(name, barcode, quantity):
    """Add a new tool with barcode and quantity."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO tools (name, barcode, quantity) VALUES (?, ?, ?)", (name, barcode, quantity))
        conn.commit()
        return {"message": "Tool added successfully"}
    except sqlite3.IntegrityError:
        return {"error": "Barcode already exists"}
    finally:
        conn.close()

def update_logout_time(logout_time):
    """Update auto-logout time in settings."""
    conn = get_db_connection()
    conn.execute("INSERT INTO settings (key, value) VALUES ('auto_logout_time', ?) ON CONFLICT(key) DO UPDATE SET value=?", 
                 (logout_time, logout_time))
    conn.commit()
    conn.close()
    return {"message": "Auto-logout time updated successfully"}

def get_logout_time():
    """Fetch auto-logout time from settings."""
    conn = get_db_connection()
    logout_time = conn.execute("SELECT value FROM settings WHERE key='auto_logout_time'").fetchone()
    conn.close()
    return int(logout_time["value"]) if logout_time else 60  # Default to 60 seconds
