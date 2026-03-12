# EyeOn Face Recognition API Integration Guide

## Overview
The updated Flask backend now supports automatic attendance recording from face recognition detection. This guide explains how to integrate your face recognition scripts with the new API.

---

## 1. AUTOMATIC ATTENDANCE RECORDING

### API Endpoint
**POST** `/api/record_attendance`

### Request Format
Send JSON data when a face is detected:

```json
{
    "detected_name": "Ayshath Nafia KM",
    "confidence": 0.95
}
```

### Parameters
- `detected_name` (string, required): Name of detected person from dataset folder
- `confidence` (float, required): Confidence score (0.0 to 1.0)

### Response - Check-In Success
```json
{
    "status": "success",
    "message": "Check-in recorded",
    "type": "check_in",
    "time": "09:15:30"
}
```

### Response - Check-Out Success
```json
{
    "status": "success",
    "message": "Check-out recorded",
    "type": "check_out",
    "time": "17:45:30"
}
```

### Response - Duplicate Detection
```json
{
    "status": "duplicate",
    "message": "Attendance already recorded within last 30 minutes"
}
```

### Error Response
```json
{
    "status": "error",
    "message": "Low confidence match"
}
```

---

## 2. PYTHON INTEGRATION EXAMPLE

### Sample Code for Face Recognition Script

```python
import requests
import cv2
import face_recognition
import pickle

# Load encodings
with open("FaceDataSheet/encodings.pkl", "rb") as f:
    data = pickle.load(f)

KNOWN_ENCODINGS = data["encodings"]
KNOWN_NAMES = data["names"]

API_URL = "http://localhost:5000/api/record_attendance"

def record_attendance(detected_name, confidence):
    """Send detected face to backend API"""
    payload = {
        "detected_name": detected_name,
        "confidence": confidence
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        result = response.json()
        
        if result["status"] == "success":
            print(f"✅ {result['message']} at {result['time']}")
        elif result["status"] == "duplicate":
            print(f"⚠️  {result['message']}")
        else:
            print(f"❌ Error: {result['message']}")
        
        return result
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return {"status": "error"}

# In your face detection loop:
def process_frame(frame):
    """Process frame and detect faces"""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)
    
    for face_encoding in face_encodings:
        # Compare with known faces
        matches = face_recognition.compare_faces(
            KNOWN_ENCODINGS, 
            face_encoding, 
            tolerance=0.6
        )
        face_distances = face_recognition.face_distance(
            KNOWN_ENCODINGS, 
            face_encoding
        )
        
        best_match_index = int(face_distances.argmin())
        
        if best_match_index < len(matches) and matches[best_match_index]:
            confidence = 1 - face_distances[best_match_index]
            detected_name = KNOWN_NAMES[best_match_index]
            
            # Record attendance via API
            if confidence > 0.6:
                result = record_attendance(detected_name, confidence)
```

---

## 3. DATABASE SCHEMA

### Attendance Table Structure
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    date TEXT NOT NULL,              -- YYYY-MM-DD format
    check_in TEXT,                   -- HH:MM:SS format
    check_out TEXT,                  -- HH:MM:SS format
    working_hours REAL DEFAULT 0,    -- Calculated hours
    status TEXT DEFAULT 'Present',   -- Present/Absent
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
    UNIQUE(employee_id, date)
);
```

### How It Works
1. **First Detection (Check-In)**
   - Creates new attendance record
   - Sets `check_in` time
   - Status = 'Present'

2. **Second Detection Same Day (Check-Out)**
   - Updates existing record
   - Sets `check_out` time
   - Calculates `working_hours`
   - Status = 'Present'

3. **Duplicate Prevention**
   - If detection within 30 minutes → ignored
   - Prevents multiple check-ins in short time

---

## 4. ATTENDANCE SUMMARY CALCULATIONS

### API Endpoint
**GET** `/api/attendance_summary`

### Response
```json
{
    "status": "success",
    "data": {
        "total_days": 22,
        "present": 20,
        "absent": 2,
        "percentage": 90.91
    }
}
```

### How It's Calculated
- **total_days**: Count of all attendance records with check_in
- **present**: Records where status='Present'
- **absent**: total_days - present
- **percentage**: (present / total_days) × 100

---

## 5. WORKING HOURS CALCULATION

### Formula
```
working_hours = (check_out_time - check_in_time) in hours
```

### Example
- Check-in: 09:00:00
- Check-out: 17:30:00
- Working Hours: 8.5 hours

---

## 6. ATTENDANCE HISTORY API

### API Endpoint
**GET** `/api/attendance_history?start_date=2026-03-01&end_date=2026-03-31`

### Response
```json
{
    "status": "success",
    "data": [
        {
            "date": "2026-03-12",
            "check_in": "09:15:30",
            "check_out": "17:45:30",
            "working_hours": 8.5,
            "status": "Present"
        },
        {
            "date": "2026-03-11",
            "check_in": "09:10:20",
            "check_out": "17:40:00",
            "working_hours": 8.5,
            "status": "Present"
        }
    ]
}
```

### Query Parameters
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)
- If no dates provided: Returns all records

---

## 7. LEAVE MANAGEMENT APIs

### Employee: Submit Leave Request
**POST** `/api/leave_request`

**Form Data:**
```
from_date: 2026-03-15
to_date: 2026-03-17
reason: Medical appointment
```

### Admin: Approve Leave
**POST** `/api/approve_leave/{leave_id}`

### Admin: Reject Leave
**POST** `/api/reject_leave/{leave_id}`

### Leave Statuses
- `pending` - Waiting for admin approval
- `approved` - Leave approved
- `rejected` - Leave rejected

---

## 8. NOTIFICATIONS SYSTEM

### Admin: Create Notification
**POST** `/api/create_notification`

**Form Data:**
```
title: System Maintenance
message: System will be down for maintenance on 2026-03-15 from 2-4 PM
```

### Get All Notifications
**GET** `/api/notifications`

**Response:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "title": "System Maintenance",
            "message": "System will be down...",
            "created_at": "2026-03-12 10:30:00"
        }
    ]
}
```

---

## 9. NAME-TO-EMPLOYEE-ID MAPPING

The system automatically maps detected names to employee IDs:

1. **Exact Match**: Compares detected name with employee.name (case-insensitive)
2. **Partial Match**: If exact match fails, checks for substring match
3. **Not Found**: Returns error if no matching employee

### Example
- Dataset folder: `Ayshath Nafia KM/`
- Employee name in DB: `Ayshath Nafia KM`
- Employee ID: `EMP001`

When face is detected as "Ayshath Nafia KM" → automatically mapped to employee_id `EMP001`

---

## 10. CURRENT DASHBOARD DATA

The employee dashboard now receives:

```python
{
    'today_attendance': {
        'check_in': '09:15:30',
        'check_out': '17:45:30',
        'working_hours': 8.5,
        'status': 'Present'
    },
    'attendance_summary': {
        'total_days': 22,
        'present': 20,
        'absent': 2,
        'percentage': 90.91
    },
    'attendance_history': [
        # Last 30 records with date, check_in, check_out, working_hours, status
    ],
    'notifications': [
        # Latest notifications
    ]
}
```

---

## 11. TESTING THE API

### Using cURL
```bash
# Test Check-In
curl -X POST http://localhost:5000/api/record_attendance \
  -H "Content-Type: application/json" \
  -d '{"detected_name": "Ayshath Nafia KM", "confidence": 0.95}'

# Get Attendance Summary
curl http://localhost:5000/api/attendance_summary

# Get Attendance History
curl "http://localhost:5000/api/attendance_history?start_date=2026-03-01&end_date=2026-03-31"
```

### Using Python Requests
```python
import requests

# Record attendance
response = requests.post(
    "http://localhost:5000/api/record_attendance",
    json={"detected_name": "John Doe", "confidence": 0.92}
)
print(response.json())

# Get summary
response = requests.get("http://localhost:5000/api/attendance_summary")
print(response.json())
```

---

## 12. ERROR CODES

| Status | Code | Meaning |
|--------|------|---------|
| success | 200 | Operation successful |
| duplicate | 200 | Attendance already recorded |
| error | 400 | Bad request / validation failed |
| not_found | 404 | Employee not found |
| unauthorized | 401 | Not logged in |
| server_error | 500 | Database/server error |

---

## 13. IMPORTANT NOTES

✅ **What the system does:**
- Automatically records check-in on first detection
- Automatically records check-out on second detection
- Calculates working hours
- Prevents duplicate entries (30-minute window)
- Maps face names to employee IDs
- Updates dashboard in real-time

✅ **Database integrity:**
- Each employee can only have one attendance record per day
- Working hours calculated automatically
- All timestamps in HH:MM:SS format
- Dates in YYYY-MM-DD format

✅ **Login still required:**
- Employees must login to dashboard to see their attendance
- Attendance is recorded regardless of login status
- Face recognition works independently

---

## 14. INTEGRATION CHECKLIST

- [ ] Face recognition script installed and working
- [ ] `requests` library installed: `pip install requests`
- [ ] Flask app running on localhost:5000
- [ ] Employee dataset created in `dataset/` folder
- [ ] Face encodings generated: `python FaceDataSheet/face_encodings.py`
- [ ] Database initialized (auto on first run)
- [ ] Test API endpoints with sample data
- [ ] Connect face recognition script to `/api/record_attendance`
- [ ] Verify attendance appears in dashboard

---

For questions or issues, check the application logs in the terminal.
