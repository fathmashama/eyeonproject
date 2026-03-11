#!/usr/bin/env python3
"""
Initialize database with employee data from CSV
"""
import sqlite3
import os
import csv

DB_PATH = "employee_dashboard.db"

def init_db():
    """Initialize database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Employees table with profile info
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Attendance table
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'present',
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, date)
        )
    """)
    
    # Leave requests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
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
            employee_id TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Database schema created successfully")

def load_employees_from_csv():
    """Load employees from CSV and populate database"""
    csv_path = "employee_info.csv"
    if not os.path.exists(csv_path):
        print("⚠ employee_info.csv not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emp_id = row.get('EmployeeID', '').strip()
            name = row.get('Name', '').strip()
            email = row.get('Email', '').strip()
            
            if emp_id and name and email:
                # Check if employee already exists
                c.execute("SELECT id FROM employees WHERE employee_id=?", (emp_id,))
                if not c.fetchone():
                    # Default username: first part of email, default password: emp_id
                    username = email.split('@')[0]
                    password = emp_id
                    department = "Engineering"
                    
                    try:
                        c.execute("""
                            INSERT INTO employees (employee_id, name, email, department, username, password)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (emp_id, name, email, department, username, password))
                    except sqlite3.IntegrityError as e:
                        print(f"⚠ Duplicate entry for {name}: {e}")
    
    conn.commit()
    
    # Count employees
    c.execute("SELECT COUNT(*) FROM employees")
    count = c.fetchone()[0]
    conn.close()
    
    print(f"✓ Loaded {count} employees from CSV")

def add_sample_attendance():
    """Add sample attendance data for testing"""
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get first employee
    c.execute("SELECT employee_id FROM employees LIMIT 1")
    result = c.fetchone()
    if result:
        emp_id = result[0]
        
        # Add sample records for last 10 days
        for i in range(10):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            check_in = f"{9+i%2}:30:00"
            check_out = f"{17+i%2}:30:00"
            
            c.execute("""
                INSERT OR IGNORE INTO attendance 
                (employee_id, date, check_in, check_out, status)
                VALUES (?, ?, ?, ?, 'present')
            """, (emp_id, date, check_in, check_out))
        
        # Add sample notification
        c.execute("""
            INSERT INTO notifications (employee_id, message, type)
            VALUES (?, ?, 'info')
        """, (emp_id, "Welcome to EyeOn! Your attendance system is now active."))
        
        conn.commit()
        print("✓ Sample attendance data added")
    
    conn.close()

def print_test_credentials():
    """Print test credentials"""
    print("\n" + "="*50)
    print("TEST CREDENTIALS")
    print("="*50)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT employee_id, name, username, password FROM employees LIMIT 5")
    rows = c.fetchall()
    conn.close()
    
    print("\nEmployee Login Credentials:")
    for emp_id, name, username, password in rows:
        print(f"  Name: {name}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print()
    
    print("Admin Login:")
    print("  Username: admin")
    print("  Password: admin123")
    print("="*50 + "\n")

if __name__ == "__main__":
    print("Initializing database...")
    
    # Remove existing database if resetting
    # if os.path.exists(DB_PATH):
    #     os.remove(DB_PATH)
    
    init_db()
    load_employees_from_csv()
    add_sample_attendance()
    print_test_credentials()
    
    print("✓ Database initialization complete!")
    print("\nYou can now run: python app.py")
