from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
import pandas as pd
import os
import json
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
            working_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, date)
        )
    """)
    
    # Check and add missing columns to attendance table
    c.execute("PRAGMA table_info(attendance)")
    existing_columns = [row[1] for row in c.fetchall()]
    
    # Add working_hours column if missing
    if 'working_hours' not in existing_columns:
        try:
            c.execute("ALTER TABLE attendance ADD COLUMN working_hours REAL DEFAULT 0")
            print("✅ Added working_hours column to attendance table")
        except Exception as e:
            print(f"Note: working_hours column - {str(e)}")
    
    # Add status column if missing
    if 'status' not in existing_columns:
        try:
            c.execute("ALTER TABLE attendance ADD COLUMN status TEXT DEFAULT 'Present'")
            print("✅ Added status column to attendance table")
        except Exception as e:
            print(f"Note: status column - {str(e)}")
    
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
    
    # Notifications table
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT DEFAULT 'admin'
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialization complete")

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

def get_employee_id_by_name(detected_name):
    """Map detected face name to employee ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Try exact match
        c.execute("SELECT employee_id FROM employees WHERE LOWER(name) = LOWER(?)", (detected_name,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        
        # Try partial match (in case of minor name variations)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT employee_id, name FROM employees")
        employees = c.fetchall()
        conn.close()
        
        detected_lower = detected_name.lower()
        for emp_id, emp_name in employees:
            if detected_lower in emp_name.lower() or emp_name.lower() in detected_lower:
                return emp_id
        
        return None
    except Exception as e:
        print(f"Error mapping name to employee ID: {e}")
        return None

def calculate_working_hours(check_in, check_out):
    """Calculate working hours between check-in and check-out"""
    try:
        if not check_in or not check_out:
            return 0
        
        time_format = "%H:%M:%S"
        check_in_time = datetime.strptime(check_in, time_format)
        check_out_time = datetime.strptime(check_out, time_format)
        
        if check_out_time < check_in_time:
            # Handle case where check-out is next day
            check_out_time = check_out_time.replace(day=check_out_time.day + 1)
        
        delta = check_out_time - check_in_time
        hours = delta.total_seconds() / 3600
        return round(hours, 2)
    except Exception as e:
        print(f"Error calculating working hours: {e}")
        return 0

def calculate_attendance_summary(employee_id):
    """Calculate attendance summary for employee"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all attendance records for employee where check_in is recorded
        c.execute("""SELECT date, check_in, check_out, 
                            COALESCE(working_hours, 0) as working_hours, 
                            COALESCE(status, 'Present') as status 
                     FROM attendance 
                     WHERE employee_id=? AND check_in IS NOT NULL""", 
                 (employee_id,))
        records = c.fetchall()
        conn.close()
        
        total_days = len(records)
        # Count present as records with check_in recorded
        present = sum(1 for record in records if record[4] == 'Present' or record[1] is not None)
        absent = total_days - present
        
        attendance_percentage = (present / total_days * 100) if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'present': present,
            'absent': absent,
            'percentage': round(attendance_percentage, 2)
        }
    except Exception as e:
        print(f"Error calculating attendance summary: {e}")
        return {'total_days': 0, 'present': 0, 'absent': 0, 'percentage': 0}

def prevent_duplicate_attendance(employee_id):
    """Check if attendance was recorded in last 30 minutes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now()
        
        c.execute("SELECT check_in, check_out FROM attendance WHERE employee_id=? AND date=?", 
                 (employee_id, today))
        attendance = c.fetchone()
        conn.close()
        
        if not attendance:
            return False  # No attendance today, allow recording
        
        check_in_str, check_out_str = attendance
        
        if check_in_str:
            try:
                check_in_time = datetime.strptime(check_in_str, "%H:%M:%S")
                # Compare with current time
                time_diff = (current_time - current_time.replace(hour=check_in_time.hour, 
                                                                   minute=check_in_time.minute, 
                                                                   second=check_in_time.second)).total_seconds() / 60
                
                # If less than 30 minutes, consider it duplicate
                if time_diff >= 0 and time_diff < 30:
                    return True
            except:
                pass
        
        return False
    except Exception as e:
        print(f"Error checking duplicate attendance: {e}")
        return False

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
        
        # Get filtered date from request (default to today)
        selected_date = request.args.get("date", today)
        
        c.execute("""SELECT check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present') 
                     FROM attendance WHERE employee_id=? AND date=?""", 
                 (employee_id, selected_date))
        today_attendance = c.fetchone()
        
        # Get attendance history for the selected date
        c.execute("""SELECT date, check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present')
                     FROM attendance WHERE employee_id=? AND date=?
                     ORDER BY date DESC""", 
                 (employee_id, selected_date))
        attendance_history = c.fetchall()
        
        # Get leave requests
        c.execute("""SELECT id, from_date, to_date, reason, status 
                     FROM leave_requests WHERE employee_id=? 
                     ORDER BY created_at DESC LIMIT 10""", 
                 (employee_id,))
        leave_requests = c.fetchall()
        
        # Get notifications (latest 5)
        c.execute("""SELECT message, created_at 
                     FROM notifications 
                     ORDER BY created_at DESC LIMIT 5""")
        notifications = c.fetchall()
        
        # DEBUG: Print notifications to console
        print("DEBUG - Notifications fetched from DB:", notifications)
        
        conn.close()
        
        # Calculate attendance summary
        attendance_summary = calculate_attendance_summary(employee_id)
        
        # Generate dynamic label for attendance section
        if selected_date == today:
            attendance_label = "Today's Attendance"
        else:
            attendance_label = f"Attendance for {selected_date}"
        
        # DEBUG: Verify notifications before passing to template
        print("DEBUG - Passing to template - notifications count:", len(notifications) if notifications else 0)
        
        return render_template(
            "employee_dashboard.html",
            employee_id=employee_id,
            employee_name=session.get("employee_name"),
            emp_info=emp_info,
            today_attendance=today_attendance,
            attendance_history=attendance_history,
            leave_requests=leave_requests,
            notifications=notifications,
            today=today,
            selected_date=selected_date,
            attendance_label=attendance_label,
            attendance_summary=attendance_summary
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

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all employees count
        c.execute("SELECT COUNT(*) FROM employees")
        total = c.fetchone()[0]
        
        # Get today's attendance
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get filtered date from request (default to today)
        selected_date = request.args.get("date", today)
        
        c.execute("""SELECT COUNT(DISTINCT employee_id) FROM attendance 
                     WHERE date=? AND check_in IS NOT NULL""", (selected_date,))
        present = c.fetchone()[0]
        
        # Calculate absent employees
        absent = total - present
        
        # Get attendance records filtered by selected date - JOIN employees and attendance
        c.execute("""SELECT e.employee_id, e.name, a.date, a.check_in, a.check_out, 
                            COALESCE(a.status, 'Present')
                     FROM attendance a
                     JOIN employees e ON e.employee_id = a.employee_id
                     WHERE a.date = ?
                     ORDER BY a.check_in DESC""", (selected_date,))
        attendance_records = c.fetchall()
        
        # Get all pending leave requests with employee names
        c.execute("""SELECT lr.id, e.name, lr.from_date, lr.to_date, lr.reason, lr.status
                     FROM leave_requests lr
                     JOIN employees e ON lr.employee_id = e.employee_id
                     ORDER BY lr.created_at DESC""")
        leave_requests = c.fetchall()
        
        # Get all registered employees
        c.execute("SELECT employee_id, name, email FROM employees")
        employees = c.fetchall()
        
        # Get list of employees present today
        c.execute("""SELECT DISTINCT e.name FROM employees e
                     JOIN attendance a ON e.employee_id = a.employee_id
                     WHERE a.date = ? AND a.check_in IS NOT NULL
                     ORDER BY e.name ASC""", (today,))
        present_today_list = [row[0] for row in c.fetchall()]
        
        # Get list of employees absent today
        c.execute("""SELECT e.name FROM employees e
                     WHERE e.employee_id NOT IN (
                        SELECT DISTINCT employee_id FROM attendance
                        WHERE date = ? AND check_in IS NOT NULL
                     )
                     ORDER BY e.name ASC""", (today,))
        absent_today_list = [row[0] for row in c.fetchall()]
        
        conn.close()
        
        # Generate HTML table from attendance records
        if attendance_records:
            table_html = '<table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">'
            table_html += '<thead style="background: rgba(255, 255, 255, 0.1); border-bottom: 2px solid var(--border-color);">'
            table_html += '<tr>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Employee ID</th>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Name</th>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Date</th>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Check-In</th>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Check-Out</th>'
            table_html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Status</th>'
            table_html += '</tr>'
            table_html += '</thead>'
            table_html += '<tbody>'
            
            for record in attendance_records:
                employee_id = record[0] or 'N/A'
                name = record[1] or 'Unknown'
                date = record[2] or 'N/A'
                check_in = record[3] or '-'
                check_out = record[4] or '-'
                status = record[5] or 'Present'
                
                table_html += '<tr style="border-bottom: 1px solid var(--border-color);">'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{employee_id}</td>'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{name}</td>'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{date}</td>'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{check_in}</td>'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{check_out}</td>'
                table_html += f'<td style="padding: 0.75rem; border: 1px solid var(--border-color);">{status}</td>'
                table_html += '</tr>'
            
            table_html += '</tbody>'
            table_html += '</table>'
        else:
            table_html = '<p style="color: var(--text-secondary); font-style: italic;">No attendance records for selected date</p>'
        
        return render_template(
            "admin_dashboard.html",
            total=total,
            present=present,
            absent=absent,
            table=table_html,
            leave_requests=leave_requests,
            employees=employees,
            present_today_list=present_today_list,
            absent_today_list=absent_today_list,
            today=today,
            selected_date=selected_date
        )
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "error")
        return redirect("/admin")

# ============= NOTIFICATION API =============
@app.route("/add_notification", methods=["POST"])
def add_notification():
    if "admin" not in session:
        return {"status": "error", "message": "Not authorized"}, 401
    
    message = request.form.get("message", "").strip()
    
    if not message:
        flash("Notification message cannot be empty!", "error")
        return redirect("/admin_dashboard")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO notifications (title, message) VALUES (?, ?)", ("Notification", message))
        conn.commit()
        conn.close()
        # DEBUG: Print inserted notification
        print("DEBUG - Notification inserted:", message)
        flash("Notification sent to all employees!", "success")
        return redirect("/admin_dashboard")
    except Exception as e:
        flash(f"Error sending notification: {str(e)}", "error")
        return redirect("/admin_dashboard")

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
    
    if not from_date or not to_date:
        flash("From date and To date are required!", "error")
        return redirect("/employee_dashboard")
    
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

# ============= ATTENDANCE RECORDING FROM FACE RECOGNITION =============
@app.route("/api/record_attendance", methods=["POST"])
def record_attendance():
    """
    API endpoint for face recognition system to record attendance
    Expected JSON: {
        "detected_name": "employee_name",
        "confidence": 0.95
    }
    """
    try:
        data = request.get_json()
        detected_name = data.get("detected_name", "").strip()
        confidence = data.get("confidence", 0)
        
        if not detected_name:
            return {"status": "error", "message": "No name detected"}, 400
        
        if confidence < 0.6:
            return {"status": "error", "message": "Low confidence match"}, 400
        
        # Get employee ID from detected name
        employee_id = get_employee_id_by_name(detected_name)
        
        if not employee_id:
            return {"status": "error", "message": f"Employee not found for name: {detected_name}"}, 404
        
        # Check for duplicate attendance within 30 minutes
        if prevent_duplicate_attendance(employee_id):
            return {"status": "duplicate", "message": "Attendance already recorded within last 30 minutes"}, 200
        
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Check if attendance record exists for today
            c.execute("SELECT check_in, check_out FROM attendance WHERE employee_id=? AND date=?", 
                     (employee_id, today))
            existing = c.fetchone()
            
            if existing:
                check_in, check_out = existing
                
                # If check-in exists but no check-out, record check-out
                if check_in and not check_out:
                    working_hours = calculate_working_hours(check_in, current_time)
                    c.execute("""UPDATE attendance 
                                SET check_out=?, working_hours=?, status='Present' 
                                WHERE employee_id=? AND date=?""",
                             (current_time, working_hours, employee_id, today))
                    conn.commit()
                    conn.close()
                    return {"status": "success", "message": "Check-out recorded", "type": "check_out", "time": current_time}, 200
                else:
                    conn.close()
                    return {"status": "duplicate", "message": "Attendance already complete for today"}, 200
            else:
                # Create new attendance record with check-in
                c.execute("""INSERT INTO attendance (employee_id, date, check_in, status)
                            VALUES (?, ?, ?, 'Present')""",
                         (employee_id, today, current_time))
                conn.commit()
                conn.close()
                return {"status": "success", "message": "Check-in recorded", "type": "check_in", "time": current_time}, 200
        
        except sqlite3.IntegrityError:
            conn.close()
            return {"status": "error", "message": "Database error"}, 500
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ============= ATTENDANCE HISTORY API =============
@app.route("/api/attendance_history", methods=["GET"])
def get_attendance_history():
    """Get filtered attendance history"""
    if "employee_id" not in session:
        return {"status": "error"}, 401
    
    employee_id = session["employee_id"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if start_date and end_date:
            c.execute("""SELECT date, check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present')
                         FROM attendance 
                         WHERE employee_id=? AND date BETWEEN ? AND ?
                         ORDER BY date DESC""",
                     (employee_id, start_date, end_date))
        else:
            c.execute("""SELECT date, check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present')
                         FROM attendance 
                         WHERE employee_id=?
                         ORDER BY date DESC""",
                     (employee_id,))
        
        records = c.fetchall()
        conn.close()
        
        history = []
        for record in records:
            history.append({
                "date": record[0],
                "check_in": record[1],
                "check_out": record[2],
                "working_hours": record[3],
                "status": record[4]
            })
        
        return {"status": "success", "data": history}, 200
    
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ============= ADMIN LEAVE MANAGEMENT =============
@app.route("/api/approve_leave/<int:leave_id>", methods=["POST"])
def approve_leave(leave_id):
    """Admin approves leave request"""
    if "admin" not in session:
        return {"status": "error", "message": "Unauthorized"}, 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("UPDATE leave_requests SET status='approved' WHERE id=?", (leave_id,))
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Leave approved"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/api/reject_leave/<int:leave_id>", methods=["POST"])
def reject_leave(leave_id):
    """Admin rejects leave request"""
    if "admin" not in session:
        return {"status": "error", "message": "Unauthorized"}, 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("UPDATE leave_requests SET status='rejected' WHERE id=?", (leave_id,))
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Leave rejected"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ============= NOTIFICATIONS MANAGEMENT =============
@app.route("/api/create_notification", methods=["POST"])
def create_notification():
    """Admin creates a new notification"""
    if "admin" not in session:
        return {"status": "error", "message": "Unauthorized"}, 401
    
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    
    if not title or not message:
        flash("Title and message are required!", "error")
        return redirect("/admin_dashboard")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""INSERT INTO notifications (title, message, created_by)
                    VALUES (?, ?, ?)""",
                 (title, message, "admin"))
        conn.commit()
        conn.close()
        
        flash("Notification created successfully!", "success")
        return redirect("/admin_dashboard")
    except Exception as e:
        flash(f"Error creating notification: {str(e)}", "error")
        return redirect("/admin_dashboard")

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get all notifications for employee"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""SELECT id, title, message, created_at 
                     FROM notifications 
                     ORDER BY created_at DESC""")
        notifications = c.fetchall()
        conn.close()
        
        data = []
        for notif in notifications:
            data.append({
                "id": notif[0],
                "title": notif[1],
                "message": notif[2],
                "created_at": notif[3]
            })
        
        return {"status": "success", "data": data}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ============= ATTENDANCE SUMMARY API =============
@app.route("/api/attendance_summary", methods=["GET"])
def get_attendance_summary():
    """Get attendance summary for employee"""
    if "employee_id" not in session:
        return {"status": "error"}, 401
    
    employee_id = session["employee_id"]
    summary = calculate_attendance_summary(employee_id)
    
    return {"status": "success", "data": summary}, 200

# ============= EMPLOYEE MANAGEMENT =============
@app.route('/delete_employee/<employee_id>')
def delete_employee(employee_id):
    """Delete employee and related attendance records"""
    if "admin" not in session:
        flash("Unauthorized access", "error")
        return redirect("/admin")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete attendance records first (to avoid foreign key issues)
        cursor.execute("DELETE FROM attendance WHERE employee_id = ?", (employee_id,))
        
        # Delete leave requests for the employee
        cursor.execute("DELETE FROM leave_requests WHERE employee_id = ?", (employee_id,))
        
        # Delete the employee
        cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        
        conn.commit()
        conn.close()
        
        flash(f"Employee {employee_id} deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting employee: {str(e)}", "error")
    
    return redirect('/admin_dashboard')

if __name__ == "__main__":
    app.run(debug=True)