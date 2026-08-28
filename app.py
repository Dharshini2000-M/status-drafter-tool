from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import date, timedelta
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create tables if they don't exist
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
            password TEXT,
            role TEXT
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass # column already exists
        
    # Add default users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('employee', 'employee', 'employee')")
        conn.commit()
    conn.close()

init_db()

# --- ROUTES ---

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("dashboard"))
    return redirect(url_for("add_status"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form.get("password", "")
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user:
            # Check if password column exists in row keys and matches, or fallback if older db without passwords
            db_pass = user["password"] if "password" in user.keys() else None
            if not db_pass or db_pass == password:
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(url_for("index"))
                
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        if not username or not password:
            return render_template("signup.html", error="Username and password are required")
            
        conn = get_db_connection()
        existing_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if existing_user:
            conn.close()
            return render_template("signup.html", error="Username already exists")
            
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'employee')", (username, password))
        conn.commit()
        conn.close()
        
        return redirect(url_for("login"))
        
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))
    
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    conn = get_db_connection()
    today_total = conn.execute("SELECT COUNT(*) FROM status WHERE status_date = ?", (today,)).fetchone()[0]
    yesterday_total = conn.execute("SELECT COUNT(*) FROM status WHERE status_date = ?", (yesterday,)).fetchone()[0]
    conn.close()
    
    return render_template("dashboard.html", today_total=today_total, yesterday_total=yesterday_total)

# --- THE FIX IS HERE ---
# Notice it says "/add_status" (underscore), NOT "/add-status"
@app.route("/add_status", methods=["GET", "POST"])
def add_status():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        status_date = request.form.get("date", date.today().isoformat())
        employee_name = request.form.get("employee_name", session["username"])
        project = request.form.get("project", "General")
        today_work = request.form.get("work_done", "")
        blockers = request.form.get("blockers", "")
        status_val = request.form.get("status")
        completed = 1 if status_val == "Completed" else 0

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO status (status_date, employee_name, project, today_work, blockers, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            status_date,
            employee_name,
            project,
            today_work,
            blockers,
            completed
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("status_list", day="today"))

    return render_template("add_status.html", today_date=date.today().isoformat(), employee_name=session["username"])

@app.route("/status/<day>")
def status_list(day):
    if "username" not in session:
        return redirect(url_for("login"))
        
    target_date = date.today().isoformat() if day == "today" else (date.today() - timedelta(days=1)).isoformat()
    title = f"{day.capitalize()}'s Status"
    
    conn = get_db_connection()
    if session.get("role") == "admin":
        rows = conn.execute("SELECT * FROM status WHERE status_date = ?", (target_date,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM status WHERE status_date = ? AND employee_name = ?", (target_date, session["username"])).fetchall()
    conn.close()
    
    return render_template("status_list.html", data=rows, title=title)

if __name__ == "__main__":

    app.run(debug=True)
