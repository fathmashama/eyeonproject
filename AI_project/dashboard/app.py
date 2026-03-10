from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time

app = Flask(__name__)
app.secret_key = "replace_this_with_a_strong_secret"  # CHANGE for production

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DB_PATH = os.path.join(BASE_DIR, "database.db")
ENCODING_FILE = os.path.join(PARENT_DIR, "FaceDataSheet", "encodings.pkl")
DATASET_PATH = os.path.join(PARENT_DIR, "dataset")

# Global variables for face recognition
face_recognition_active = False
captured_face_name = None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create DB and tables if they don't exist and add a default admin."""
    conn = get_db()
    cur = conn.cursor()
    # Admins table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    # Employees table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            WorkerID TEXT UNIQUE,
            name TEXT,
            email TEXT
        )
    """)
    # Attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            WorkerID TEXT,
            name TEXT,
            date TEXT,
            time TEXT
        )
    """)
    # Add default admin if not exists
    cur.execute("SELECT * FROM admins WHERE username=?", ("admin",))
    if not cur.fetchone():
        default_pw = "admin123"
        pw_hash = generate_password_hash(default_pw)
        cur.execute("INSERT INTO admins (username, password_hash) VALUES (?,?)", ("admin", pw_hash))
        print("[init_db] Default admin created -> username: admin  password:", default_pw)
    conn.commit()
    conn.close()

def load_face_encodings():
    """Load pre-trained face encodings if available."""
    if os.path.exists(ENCODING_FILE):
        try:
            with open(ENCODING_FILE, "rb") as f:
                data = pickle.load(f)
            return data.get("encodings", []), data.get("names", [])
        except:
            return [], []
    return [], []

@app.route("/")
def index():
    if "admin" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=?", (username,))
        admin = cur.fetchone()
        conn.close()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees")
    total = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT WorkerID) FROM attendance WHERE date = date('now')")
    present = cur.fetchone()[0] or 0
    absent = total - present
    conn.close()
    return render_template("dashboard.html", total=total, present=present, absent=absent, admin=session.get("admin"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        worker_id = request.form.get("worker_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        
        if not worker_id or not name:
            flash("Worker ID and Name are required!", "danger")
            return render_template("employees.html")
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO employees (WorkerID, name, email) VALUES (?, ?, ?)", 
                       (worker_id, name, email))
            conn.commit()
            flash(f"Employee {name} registered successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Worker ID already exists!", "danger")
        finally:
            conn.close()
        
        return render_template("employees.html")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    conn.close()
    
    return render_template("employees.html", employees=employees)

@app.route("/api/start-face-capture", methods=["POST"])
def start_face_capture():
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    global face_recognition_active
    face_recognition_active = True
    return jsonify({"status": "Face recognition started"}), 200

@app.route("/api/stop-face-capture", methods=["POST"])
def stop_face_capture():
    global face_recognition_active
    face_recognition_active = False
    return jsonify({"status": "Face recognition stopped"}), 200

@app.route("/attendance")
def attendance():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cur = conn.cursor()
    # Get today's attendance records
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT * FROM attendance WHERE date = ? ORDER BY time DESC", (today,))
    records = cur.fetchall()
    conn.close()
    
    return render_template("attendance.html", records=records, today=today)

@app.route("/api/run-recognition", methods=["POST"])
def run_recognition():
    """Run live face recognition and mark attendance."""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Load encodings
        known_encodings, known_names = load_face_encodings()
        
        if not known_encodings:
            return jsonify({"error": "No pre-trained faces found. Please capture faces first."}), 400
        
        # Start webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return jsonify({"error": "Cannot access webcam"}), 400
        
        marked_today = set()
        found_faces = []
        frame_count = 0
        max_frames = 150  # Process for ~5 seconds at 30 fps
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                
                if len(distances) > 0:
                    best_match_idx = np.argmin(distances)
                    if matches[best_match_idx]:
                        name = known_names[best_match_idx]
                        
                        if name not in marked_today:
                            # Get employee info
                            conn = get_db()
                            cur = conn.cursor()
                            cur.execute("SELECT WorkerID FROM employees WHERE name = ?", (name,))
                            employee = cur.fetchone()
                            
                            if employee:
                                worker_id = employee[0]
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                date = datetime.now().strftime("%Y-%m-%d")
                                time = datetime.now().strftime("%H:%M:%S")
                                
                                cur.execute(
                                    "INSERT INTO attendance (WorkerID, name, date, time) VALUES (?, ?, ?, ?)",
                                    (worker_id, name, date, time)
                                )
                                conn.commit()
                                marked_today.add(name)
                                found_faces.append(name)
                            
                            conn.close()
        
        cap.release()
        
        return jsonify({
            "status": "Recognition complete",
            "marked_faces": list(found_faces),
            "count": len(found_faces)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    else:
        # ensure tables exist and default admin exists
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
