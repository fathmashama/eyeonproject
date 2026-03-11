from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "eyeon_secret_attendance_2025"

# Database path
DB_PATH = "employee_database.db"

# ============= DATABASE SETUP =============
def init_db():
    """Initialize database with updated schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if employees table exists and has username column
    c.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in c.fetchall()]
    
    # Drop old table if it exists without username column
    if 'employees' in [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        if 'username' not in columns:
            c.execute("DROP TABLE IF EXISTS employees")
    
    # Employees table with new schema
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Attendance table with proper structure
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, date)
        )
    """)
    
    # Leave requests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        )
    """)
    
    conn.commit()
    conn.close()

def init_attendance_csv():
    if not os.path.exists("attendance.csv"):
        df = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "DateTime"])
        df.to_csv("attendance.csv", index=False)

def get_dataset_folders():
    """Get list of employee folders in dataset directory"""
    dataset_path = "dataset"
    if not os.path.exists(dataset_path):
        return []
    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    return folders

def get_valid_employee_ids():
    """Get valid employee IDs from employee_info.csv"""
    valid_ids = {}
    try:
        if os.path.exists("employee_info.csv"):
            df = pd.read_csv("employee_info.csv")
            for _, row in df.iterrows():
                valid_ids[row['EmployeeID']] = {
                    'name': row['Name'],
                    'email': row['Email']
                }
    except Exception as e:
        print(f"Error reading employee_info.csv: {e}")
    return valid_ids

init_db()
init_attendance_csv()

# ============= HOME PAGE =============
@app.route("/")
def home():
    return render_template("employee_login.html")

# ============= EMPLOYEE REGISTRATION =============
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip()
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        # Validation
        if not all([employee_id, username, name, email, phone, password, confirm_password]):
            flash("All fields are required!", "error")
            return redirect("/register")
        
        if len(username) < 4:
            flash("Username must be at least 4 characters long!", "error")
            return redirect("/register")
        
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect("/register")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long!", "error")
            return redirect("/register")
        
        # Check if Employee ID is valid
        valid_employees = get_valid_employee_ids()
        if employee_id not in valid_employees:
            available_ids = ", ".join(list(valid_employees.keys())[:5])
            flash(f"Invalid Employee ID. Available IDs: {available_ids}...", "error")
            return redirect("/register")
        
        # Verify the name matches the employee record
        if valid_employees[employee_id]['name'] != name:
            flash(f"Name does not match the registered name for Employee ID {employee_id}. Expected: {valid_employees[employee_id]['name']}", "error")
            return redirect("/register")
        
        # Hash password and insert into database
        try:
            password_hash = generate_password_hash(password)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO employees (employee_id, username, name, email, phone, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (employee_id, username, name, email, phone, password_hash))
            conn.commit()
            conn.close()
            
            flash("Registration successful! Please log in with your username.", "success")
            return redirect("/")
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                flash("Username already taken! Choose a different username.", "error")
            elif "email" in str(e):
                flash("Email already registered!", "error")
            else:
                flash("Employee ID or Email already registered!", "error")
            return redirect("/register")
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")
            return redirect("/register")
    
    # GET request - show registration form
    valid_employees = get_valid_employee_ids()
    return render_template("employee_register.html", valid_employees=valid_employees)

# ============= EMPLOYEE LOGIN =============
@app.route("/employee_login", methods=["POST"])
def employee_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    
    if not username or not password:
        flash("Username and password are required!", "error")
        return redirect("/")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT employee_id, name, password_hash FROM employees WHERE username=?", (username,))
        employee = c.fetchone()
        conn.close()
        
        if employee and check_password_hash(employee[2], password):
            session["employee_id"] = employee[0]
            session["employee_name"] = employee[1]
            session["username"] = username
            return redirect("/employee_dashboard")
        else:
            flash("Invalid username or password!", "error")
            return redirect("/")
    except Exception as e:
        flash(f"Login error: {str(e)}", "error")
        return redirect("/")

@app.route("/employee_dashboard")
def employee_dashboard():
    if "employee_id" not in session:
        return redirect("/")
    
    employee_id = session["employee_id"]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get employee info
        c.execute("SELECT name, email, phone FROM employees WHERE employee_id=?", (employee_id,))
        emp_info = c.fetchone()
        
        # Get today's attendance
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT check_in, check_out FROM attendance WHERE employee_id=? AND date=?", 
                 (employee_id, today))
        today_attendance = c.fetchone()
        
        # Get attendance history
        c.execute("SELECT date, check_in, check_out FROM attendance WHERE employee_id=? ORDER BY date DESC LIMIT 30", 
                 (employee_id,))
        attendance_history = c.fetchall()
        
        # Get leave requests
        c.execute("SELECT from_date, to_date, reason, status FROM leave_requests WHERE employee_id=? ORDER BY created_at DESC LIMIT 10", 
                 (employee_id,))
        leave_requests = c.fetchall()
        
        conn.close()
        
        return render_template(
            "employee_dashboard.html",
            employee_id=employee_id,
            employee_name=session.get("employee_name"),
            emp_info=emp_info,
            today_attendance=today_attendance,
            attendance_history=attendance_history,
            leave_requests=leave_requests,
            today=today
        )
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "error")
        return redirect("/")

# ============= ADMIN LOGIN =============
@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "admin123":
        session["admin"] = username
        return redirect("/admin_dashboard")
    else:
        flash("Invalid Admin Credentials", "error")
        return redirect("/admin")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    init_attendance_csv()
    df = pd.read_csv("attendance.csv")
    total = df["Name"].nunique()

    today = datetime.now().strftime("%Y-%m-%d")
    df["Date"] = df["DateTime"].str[:10]
    today_df = df[df["Date"] == today]
    present = today_df["Name"].nunique()

    return render_template(
        "admin_dashboard.html",
        total=total,
        present=present,
        table=df.to_html(classes="table table-striped", index=False)
    )

# ============= LOGOUT =============
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ============= LEAVE REQUEST API =============
@app.route("/api/leave_request", methods=["POST"])
def leave_request():
    if "employee_id" not in session:
        return {"status": "error", "message": "Not logged in"}, 401
    
    employee_id = session["employee_id"]
    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")
    reason = request.form.get("reason", "")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO leave_requests (employee_id, from_date, to_date, reason)
            VALUES (?, ?, ?, ?)
        """, (employee_id, from_date, to_date, reason))
        conn.commit()
        conn.close()
        flash("Leave request submitted successfully!", "success")
        return redirect("/employee_dashboard")
    except Exception as e:
        flash(f"Error submitting leave request: {str(e)}", "error")
        return redirect("/employee_dashboard")

if __name__ == "__main__":
    app.run(debug=True)