# 🎯 Face Recognition Database Integration Guide

## Overview

The `real_attend2.py` script has been updated to **write attendance directly to the SQLite database** instead of Excel/text files. This connects face recognition with the Flask dashboards.

**Status:** ✅ **READY TO USE**

---

## What Changed

### ❌ REMOVED
- Excel file writing (`AttendanceRecords/*.xlsx`)
- Text file writing (`AttendanceRecords/*.txt`)
- CSV file writing (`attendance.csv`)
- Employee info CSV loading (no longer needed)

### ✅ ADDED
- Direct SQLite database connections
- Automatic check-in/check-out logic (no manual entry needed)
- Working hours calculation
- Database employee lookup by name
- Real-time attendance recording

---

## How It Works Now

### 1️⃣ Face Detected
```
Webcam → Face Recognition → Detected Name (from encodings.pkl)
```

### 2️⃣ Look Up Employee ID
```
Detected Name → Query Database → Get employee_id from employees table
                (case-insensitive lookup)
```

### 3️⃣ Record Attendance

**First Detection (Check-In):**
```
✅ INSERT INTO attendance (employee_id, date, check_in, status)
   VALUES ('2023B144', '2026-03-12', '09:15:30', 'Present')
```

**Second Detection (Check-Out):**
```
✅ UPDATE attendance SET check_out='17:45:20', working_hours=8.5
   WHERE employee_id='2023B144' AND date='2026-03-12'
```

### 4️⃣ Dashboards Display Data
```
Employee Dashboard → See today's check-in/out, working hours
Admin Dashboard → See all employees' attendance
```

---

## Database Schema

### Attendance Table

```sql
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    date TEXT NOT NULL,              -- YYYY-MM-DD format
    check_in TEXT,                   -- HH:MM:SS format (set on first detection)
    check_out TEXT,                  -- HH:MM:SS format (set on second detection)
    working_hours REAL DEFAULT 0,    -- Auto-calculated (check_out - check_in)
    status TEXT DEFAULT 'Present',   -- Present/Absent
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
    UNIQUE(employee_id, date)        -- One record per employee per day
)
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `employee_id` | TEXT | Links to employees table (e.g., '2023B144') |
| `date` | TEXT | Day of attendance (YYYY-MM-DD) |
| `check_in` | TEXT | Time employee entered (HH:MM:SS) |
| `check_out` | TEXT | Time employee left (HH:MM:SS) |
| `working_hours` | REAL | Auto-calculated hours worked |
| `status` | TEXT | 'Present' (default) |

---

## Updated Script: real_attend2.py

### Key Functions

#### 1. `get_employee_id_by_name(detected_name)`
**Purpose:** Map detected face name to employee_id
```python
def get_employee_id_by_name(detected_name):
    # Queries: SELECT employee_id FROM employees 
    #          WHERE LOWER(name) = LOWER(detected_name)
    
    return employee_id  # e.g., '2023B144'
```

**How it works:**
- Takes detected name from face recognition
- Queries employees table (case-insensitive)
- Returns employee_id string or None if not found

**Example:**
```
Input:  "Ayshath Nafia KM"
Output: "2023B144"
```

#### 2. `calculate_working_hours(check_in, check_out)`
**Purpose:** Calculate hours worked between times
```python
def calculate_working_hours(check_in, check_out):
    # Input: "09:15:30", "17:45:20"
    # Calculates difference
    # Output: 8.5
    
    return 8.5  # hours as float
```

**How it works:**
- Parses HH:MM:SS times
- Calculates difference in hours
- Returns float with 2 decimal places

**Example:**
```
Check-in:  09:15:30
Check-out: 17:45:20
Hours:     8.5 (8 hours 30 minutes)
```

#### 3. `record_attendance(employee_id, detected_name, current_date, current_time)`
**Purpose:** Insert or update attendance in database
```python
def record_attendance(employee_id, detected_name, current_date, current_time):
    # First detection: INSERT check_in
    # Second detection: UPDATE check_out + working_hours
    # Subsequent detections: SKIP (already checked out)
    
    return "check_in" | "check_out" | "duplicate" | "error"
```

**Logic Flow:**

```
Does today's record exist for this employee?
│
├─ NO:  INSERT check_in → Return "check_in"
│       First detection of the day = Employee arrived
│
└─ YES: Does check_out exist?
       │
       ├─ NO:  UPDATE check_out + working_hours → Return "check_out"
       │       Second detection = Employee departing
       │
       └─ YES: SKIP → Return "duplicate"
              Already checked out, no more updates
```

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FACE RECOGNITION SCRIPT                  │
│                     (real_attend2.py)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Face Detected   │
                    │  (from webcam)   │
                    └────────┬─────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │ Confidence > 0.45?         │
                │ (Match in known_encodings) │
                └────────┬────────────────────┘
                         │YES
                         ▼
            ┌─────────────────────────────┐
            │ Get Detected Name           │
            │ (from known_names array)    │
            └────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ Query: Get employee_id by name │
        │ SELECT employee_id FROM        │
        │ employees WHERE LOWER(name)... │
        └────────┬───────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────┐
    │ Found employee_id?                 │
    └────────┬──────────────┬────────────┘
           YES              NO
             │               └─→ Print warning, SKIP
             │
             ▼
    ┌──────────────────────────────────┐
    │ record_attendance()               │
    │ (employee_id, name, date, time)  │
    └────────┬─────────────────────────┘
             │
             ├─→ Check if today's record exists
             │
             ├─NO:  INSERT check_in
             │      ✅ CHECK-IN recorded
             │
             └─YES: Check if check_out exists
                    ├─NO:  UPDATE check_out + hours
                    │      ✅ CHECK-OUT recorded
                    │
                    └─YES: SKIP (already done)
```

---

## Running the Script

### Prerequisites
```bash
# Ensure dependencies are installed
pip install opencv-python face_recognition dlib numpy

# Verify database exists
# (Flask app creates it on first run)
```

### Start Face Recognition
```bash
python real_attend2.py
```

### Console Output Example
```
✅ Encodings loaded.
📷 Webcam started. Press 'q' to quit.
🔍 Detected: Ayshath Nafia KM
✅ CHECK-IN: Ayshath Nafia KM | 2026-03-12 | 09:15:30

[Point camera at another employee]

🔍 Detected: Monika Devi
✅ CHECK-IN: Monika Devi | 2026-03-12 | 09:20:15

[Same employee returns later]

🔍 Detected: Ayshath Nafia KM
✅ CHECK-OUT: Ayshath Nafia KM | 2026-03-12 | 17:45:20 | Hours: 8.5

[Press 'q' to quit]

👋 Webcam closed.
```

### Stopping the Script
```
Press 'q' key to quit gracefully
```

---

## Employee Dashboard - Data Display

### What Employee Sees

**Today's Attendance Card:**
```
┌─────────────────────────────┐
│   Today's Attendance        │
├─────────────────────────────┤
│ Check-In:     09:15:30      │
│ Check-Out:    17:45:20      │
│ Working Hours: 8.5          │
│ Status:       Present       │
└─────────────────────────────┘
```

**Attendance History Table:**
```
Date       | Check-In  | Check-Out | Hours | Status
-----------|-----------|-----------|-------|--------
2026-03-12 | 09:15:30  | 17:45:20  | 8.5   | Present
2026-03-11 | 09:10:15  | 17:30:00  | 8.33  | Present
2026-03-10 | 08:45:00  | 17:00:00  | 8.25  | Present
```

**Attendance Summary:**
```
Total Days:  30
Present:     29
Absent:      1
Percentage:  96.67%
```

### How Data Flows to Dashboard

```
Face Recognition (real_attend2.py)
    │
    ▼
SQLite Database (attendance table)
    │
    ▼
Flask Route: /employee_dashboard
    │
    ├─ Query: SELECT * FROM attendance WHERE employee_id = ? (today)
    ├─ Query: SELECT * FROM attendance WHERE employee_id = ? (history)
    ├─ Query: Calculate statistics
    │
    ▼
employee_dashboard.html (renders data)
    │
    ▼
Employee Browser (sees attendance)
```

---

## Admin Dashboard - Data Display

### What Admin Sees

**Dashboard Summary:**
```
┌──────────────────────────────┐
│  Total Employees:      8     │
│  Present Today:        6     │
└──────────────────────────────┘
```

**Full Attendance Logs Table:**
```
Employee ID | Name              | Date       | Check-In  | Check-Out | Hours | Status
------------|-------------------|------------|-----------|-----------|-------|--------
2023B144    | Ayshath Nafia KM  | 2026-03-12 | 09:15:30  | 17:45:20  | 8.5   | Present
2023B098    | Monika Devi       | 2026-03-12 | 09:20:15  | 17:30:00  | 8.17  | Present
2023B060    | Meenu PP          | 2026-03-12 | 08:45:00  | 17:00:00  | 8.25  | Present
```

### How Data Flows to Admin Dashboard

```
Face Recognition (real_attend2.py)
    │
    ▼
SQLite Database (attendance table)
    │
    ▼
Flask Route: /admin_dashboard
    │
    ├─ Query: SELECT COUNT(*) FROM employees
    ├─ Query: SELECT * FROM attendance (all, ordered by date DESC)
    ├─ Query: SELECT * FROM leave_requests
    ├─ Query: SELECT * FROM notifications
    │
    ▼
admin_dashboard.html (renders data)
    │
    ▼
Admin Browser (sees all attendance)
```

---

## Database Queries Used

### In real_attend2.py

**Get Employee ID:**
```sql
SELECT employee_id FROM employees 
WHERE LOWER(name) = LOWER(?)
```

**Check Today's Record:**
```sql
SELECT id, check_in, check_out FROM attendance 
WHERE employee_id=? AND date=?
```

**Insert Check-In:**
```sql
INSERT INTO attendance (employee_id, date, check_in, status) 
VALUES (?, ?, ?, 'Present')
```

**Update Check-Out:**
```sql
UPDATE attendance 
SET check_out=?, working_hours=? 
WHERE id=?
```

### In Flask (app.py)

**Employee Dashboard - Today's Attendance:**
```sql
SELECT check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present') 
FROM attendance 
WHERE employee_id=? AND date=?
```

**Employee History:**
```sql
SELECT date, check_in, check_out, COALESCE(working_hours, 0), COALESCE(status, 'Present')
FROM attendance 
WHERE employee_id=? 
ORDER BY date DESC LIMIT 30
```

**Admin Dashboard - All Attendance:**
```sql
SELECT e.employee_id, e.name, a.date, a.check_in, a.check_out, 
       COALESCE(a.working_hours, 0), COALESCE(a.status, 'Present')
FROM employees e 
LEFT JOIN attendance a ON e.employee_id = a.employee_id
ORDER BY a.date DESC LIMIT 100
```

---

## Important Features

### ✅ Automatic Check-In/Check-Out
- **No manual entry needed**
- First detection of day = Check-in
- Second detection later = Check-out
- Cannot check-in twice (prevents duplicates)

### ✅ Working Hours Auto-Calculation
- **Formula:** Check-out time - Check-in time
- **Format:** Hours as decimal (e.g., 8.5 = 8 hours 30 minutes)
- **Stored:** In `working_hours` field of attendance table

### ✅ Prevents Duplicate Recording
- **5-minute buffer:** Same person detected within 5 minutes = ignored
- **Same-day rule:** Only one check-out per day per employee
- **Prevents:** Multiple check-in entries for same person

### ✅ Case-Insensitive Name Matching
- **"Ayshath Nafia KM"** = **"ayshath nafia km"** (no difference)
- Handles any case variation in detected names

### ✅ Real-Time Updates
- **Face detected** → Database updated immediately
- **Dashboard refresh** → Shows latest attendance
- **No delay** between detection and database record

---

## Troubleshooting

### Issue: "Employee not found in database"
**Cause:** Name in face encodings doesn't match name in employees table

**Solution:**
1. Open employees table: `sqlite3 employee_database.db`
2. Check spelling: `SELECT name FROM employees;`
3. Regenerate encodings if name mismatch
4. Ensure employee registered in Flask registration form

### Issue: Working hours shows 0
**Cause:** Employee hasn't checked out yet, or times are invalid

**Solution:**
- Check-out happens on second detection
- Ensure webcam detects employee again later
- Check time formats are HH:MM:SS

### Issue: Attendance not showing on dashboard
**Cause:** Database not updated, or dashboard not refreshed

**Solution:**
1. Run script: `python real_attend2.py`
2. Ensure face detected (check console output)
3. Refresh dashboard in browser (Ctrl+F5)
4. Check employee_database.db exists

### Issue: Face not recognized
**Cause:** Confidence too low (> 0.45 threshold)

**Solution:**
- Better lighting on face
- Face directly toward camera
- Ensure encodings.pkl generated properly
- Run face_encodings.py to regenerate

---

## Step-By-Step Usage

### 1. Start Flask App
```bash
python app.py
```
Output:
```
✅ Database initialization complete
Running on http://127.0.0.1:5000
```

### 2. In Another Terminal, Start Face Recognition
```bash
python real_attend2.py
```
Output:
```
✅ Encodings loaded.
📷 Webcam started. Press 'q' to quit.
```

### 3. Face Detection Starts
- Point webcam at employee
- System detects → Records check-in
- Script shows: `✅ CHECK-IN: [Name] | [Date] | [Time]`

### 4. Employee Checks Out
- Same employee detected again later (different time)
- System calculates hours worked
- Script shows: `✅ CHECK-OUT: [Name] | [Date] | [Time] | Hours: [X.X]`

### 5. View on Dashboard
- Go to: `http://localhost:5000`
- Login as employee
- Dashboard shows today's attendance and history

### 6. Admin View
- Login as admin (admin/admin123)
- Admin dashboard shows all employee attendance
- Refreshes automatically (data from database)

### 7. Stop Face Recognition
- Press 'q' key in terminal
- Output: `👋 Webcam closed.`

---

## Integration Checklist

- ✅ Face recognition writes to database (not files)
- ✅ Check-in/check-out logic implemented
- ✅ Working hours auto-calculation enabled
- ✅ Employee dashboard displays attendance
- ✅ Admin dashboard displays all attendance
- ✅ Duplicate detection within 5 minutes
- ✅ Case-insensitive name matching
- ✅ Real-time data updates
- ✅ Login/registration unchanged
- ✅ Admin credentials safe (admin/admin123)

---

## Files Modified

| File | Change | Status |
|------|--------|--------|
| real_attend2.py | Complete rewrite for database integration | ✅ Complete |
| app.py | No changes (already has database code) | ✅ Ready |
| employees table | No changes | ✅ Safe |
| Login system | No changes | ✅ Safe |

---

## Next Steps

1. ✅ **Start Flask app** → `python app.py`
2. ✅ **Verify dashboard loads** → `http://localhost:5000`
3. ✅ **Run face recognition** → `python real_attend2.py`
4. ✅ **Test attendance recording** → Point at faces
5. ✅ **Check dashboards** → Login and view data
6. ✅ **Monitor database** → Attendance updates in real-time

---

## Support

**All queries below work on the updated system:**

- How do I see attendance data? → Check employee dashboard (after logging in)
- How does working hours calculate? → Check-out time - Check-in time
- Can I manual enter attendance? → No (automated by face detection)
- How do I check database? → `sqlite3 employee_database.db`
- Can I use both old files and database? → No (now database-only)

---

**Status:** ✅ Face Recognition Fully Integrated with Database
**Date Updated:** March 12, 2026
**Version:** 2.0 (Database Integration)
