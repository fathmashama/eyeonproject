import cv2
import face_recognition
import pickle
import os
import numpy as np
import sqlite3
from datetime import datetime, timedelta

# ============= DATABASE SETUP =============
DB_PATH = "employee_database.db"

def get_employee_id_by_name(detected_name):
    """Get employee_id from employees table by name (case-insensitive)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Try exact match first (case-insensitive)
        c.execute("SELECT employee_id FROM employees WHERE LOWER(name) = LOWER(?)", (detected_name,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"❌ Error getting employee ID: {e}")
        return None

def calculate_working_hours(check_in, check_out):
    """Calculate working hours from check_in and check_out times (HH:MM:SS format)"""
    try:
        if not check_in or not check_out:
            return 0
        
        # Parse times
        check_in_obj = datetime.strptime(check_in, "%H:%M:%S")
        check_out_obj = datetime.strptime(check_out, "%H:%M:%S")
        
        # Calculate difference
        delta = check_out_obj - check_in_obj
        hours = delta.total_seconds() / 3600
        
        return round(hours, 2)
    except Exception as e:
        print(f"❌ Error calculating working hours: {e}")
        return 0

def record_attendance(employee_id, detected_name, current_date, current_time):
    """Record or update attendance in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if employee already has attendance record for today
        c.execute("""SELECT id, check_in, check_out FROM attendance 
                     WHERE employee_id=? AND date=?""", 
                 (employee_id, current_date))
        record = c.fetchone()
        
        if not record:
            # First detection = Check-in
            c.execute("""INSERT INTO attendance (employee_id, date, check_in, status) 
                         VALUES (?, ?, ?, 'Present')""",
                     (employee_id, current_date, current_time))
            conn.commit()
            conn.close()
            print(f"✅ CHECK-IN: {detected_name} | {current_date} | {current_time}")
            return "check_in"
        
        else:
            # Record exists
            record_id, check_in_time, check_out_time = record
            
            if check_out_time is None:
                # Check-out not recorded yet
                # Calculate working hours
                working_hours = calculate_working_hours(check_in_time, current_time)
                
                # Update with check-out
                c.execute("""UPDATE attendance 
                            SET check_out=?, working_hours=? 
                            WHERE id=?""",
                         (current_time, working_hours, record_id))
                conn.commit()
                conn.close()
                print(f"✅ CHECK-OUT: {detected_name} | {current_date} | {current_time} | Hours: {working_hours}")
                return "check_out"
            else:
                # Both check-in and check-out already recorded
                conn.close()
                return "duplicate"
        
    except Exception as e:
        print(f"❌ Error recording attendance: {e}")
        return "error"

# Load encodings
with open("FaceDataSheet/encodings.pkl", "rb") as file:
    data = pickle.load(file)
    known_encodings = data["encodings"]
    known_names = data["names"]

print("✅ Encodings loaded.")

# Initialize webcam
video = cv2.VideoCapture(0)
print("📷 Webcam started. Press 'q' to quit.")

# Initialize tracking variables
last_seen = {}
delay = timedelta(minutes=5)

while True:
    ret, frame = video.read()
    if not ret:
        break

    if frame is None or frame.size == 0:
        continue

    # Handle 4-channel (BGRA) frames from some webcams
    if len(frame.shape) == 3 and frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Ensure the image is contiguous uint8 (required by dlib)
    if rgb_frame.dtype != np.uint8:
        rgb_frame = rgb_frame.astype(np.uint8)
    if not rgb_frame.flags['C_CONTIGUOUS']:
        rgb_frame = np.ascontiguousarray(rgb_frame)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            min_distance = face_distances[best_match_index]

            if min_distance < 0.45:
                name = known_names[best_match_index]
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                current_date = now.strftime("%Y-%m-%d")
                timestamp_str = f"{name} | {current_date} | {current_time}"

                if name not in last_seen or now - last_seen[name] > delay:
                    print(f"🔍 Detected: {name}")
                    last_seen[name] = now
                    
                    # Get employee_id from database
                    employee_id = get_employee_id_by_name(name)
                    
                    if employee_id:
                        # Record attendance in database
                        result = record_attendance(employee_id, name, current_date, current_time)
                    else:
                        print(f"⚠️  Employee not found in database: {name}")

        # Draw box and name
        top, right, bottom, left = face_location
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

    cv2.imshow("Attendance System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
print("👋 Webcam closed.")
