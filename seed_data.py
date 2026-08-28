import sqlite3
from datetime import date, timedelta

# 1. Connect to database (creates the file if missing)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# --- FIX: Create Tables First ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_date TEXT,
        employee_name TEXT,
        project TEXT,
        today_work TEXT,
        blockers TEXT,
        completed INTEGER
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        role TEXT
    )
""")

# Create default users if they don't exist
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO users (username, role) VALUES ('admin', 'admin')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('employee', 'employee')")
    print("Created default users (admin/admin, employee/employee)")

# --- END FIX ---

# 2. Calculate Yesterday's Date
yesterday = (date.today() - timedelta(days=1)).isoformat()

# 3. Clear old data for yesterday (so we don't have duplicates)
cursor.execute("DELETE FROM status WHERE status_date = ?", (yesterday,))

# 4. Insert Dummy Data for Yesterday
print(f"Adding data for date: {yesterday}...")

cursor.execute("""
    INSERT INTO status (status_date, employee_name, project, today_work, blockers, completed)
    VALUES (?, ?, ?, ?, ?, ?)
""", (yesterday, "jayaprakash", "AI Chatbot", "Designed the conversation flow", "None", 1))

cursor.execute("""
    INSERT INTO status (status_date, employee_name, project, today_work, blockers, completed)
    VALUES (?, ?, ?, ?, ?, ?)
""", (yesterday, "subha", "Frontend UI", "Fixed alignment issues in CSS", "Waiting for API", 0))

# 5. Save and Close
conn.commit()
conn.close()

print("✅ Success! Database initialized and dummy data added.")