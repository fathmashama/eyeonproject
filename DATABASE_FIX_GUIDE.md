# Database Schema Fix - EyeOn Attendance System

## Problem
The Flask app was throwing error: `Dashboard error: no such column: working_hours`

This happened because:
1. The old `attendance` table didn't have the `working_hours` column
2. The app code was trying to query this non-existent column
3. The CREATE TABLE IF NOT EXISTS statement doesn't add missing columns to existing tables

## Solution Applied

### 1. Updated `app.py` - Enhanced `init_db()` Function ✅

The database initialization function now:
- ✅ Creates new tables if they don't exist (as before)
- ✅ **NEW:** Checks for existing `attendance` table structure
- ✅ **NEW:** Uses `ALTER TABLE` to safely add missing columns:
  - `working_hours REAL DEFAULT 0`
  - `status TEXT DEFAULT 'Present'`
- ✅ **Preserves all existing data** - No records deleted
- ✅ **Non-destructive** - Doesn't drop tables

**Code Change:**
```python
# NEW: Check and add missing columns to attendance table
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
```

### 2. Updated All Database Queries - Handle NULL Values ✅

All database queries now use `COALESCE()` to handle NULL values for old records:

**Before:**
```python
SELECT date, check_in, check_out, working_hours, status 
FROM attendance
```

**After:**
```sql
SELECT date, check_in, check_out, 
       COALESCE(working_hours, 0) as working_hours, 
       COALESCE(status, 'Present') as status 
FROM attendance
```

### 3. Updated Routes with NULL Handling ✅

**Routes Updated:**
- ✅ `employee_dashboard()` - Uses COALESCE for working_hours and status
- ✅ `admin_dashboard()` - Uses COALESCE for working_hours and status  
- ✅ `get_attendance_history()` - API endpoint with COALESCE
- ✅ `calculate_attendance_summary()` - Handles NULL values in calculations

### 4. Created Migration Utility ✅

File: `migrate_db.py`

**Purpose:** Safely migrate existing database to new schema

**Usage:**
```bash
python migrate_db.py
```

**What it does:**
- ✅ Checks if database exists
- ✅ Lists all existing columns
- ✅ Adds missing columns safely
- ✅ Preserves all data
- ✅ Verifies migration success
- ✅ Reports NULL values in old records

---

## How to Apply the Fix

### Option 1: Automatic (Recommended) ✅
Simply run the app - `init_db()` will auto-fix on startup:
```bash
python app.py
```

The database will automatically:
1. Check if columns exist
2. Add missing columns
3. Preserve all data
4. Print confirmation messages

### Option 2: Manual Migration
Run the migration script:
```bash
python migrate_db.py
```

This will:
1. Check current schema
2. Display current columns
3. Add missing columns
4. Verify the migration
5. Show data integrity report

---

## What Was Fixed

| Issue | Solution | Status |
|-------|----------|--------|
| `working_hours` column missing | ALTER TABLE ADD COLUMN | ✅ Fixed |
| `status` column missing | ALTER TABLE ADD COLUMN | ✅ Fixed |
| NULL values in old records | COALESCE in all queries | ✅ Fixed |
| Dashboard error on load | Updated all routes | ✅ Fixed |
| Data loss risk | No table drops, ALTER TABLE only | ✅ Safe |
| Login/registration affected | No changes to employees table | ✅ Untouched |

---

## Database Schema Now Contains

### attendance table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    date TEXT NOT NULL,
    check_in TEXT,
    check_out TEXT,
    working_hours REAL DEFAULT 0,              -- ✅ Added
    status TEXT DEFAULT 'Present',             -- ✅ Added
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
    UNIQUE(employee_id, date)
)
```

### Additional Tables (Unchanged)
- ✅ `employees` - No changes
- ✅ `leave_requests` - No changes
- ✅ `notifications` - Already existed

---

## Verification

After applying the fix, verify the dashboard works:

1. **Start the app:**
   ```bash
   python app.py
   ```

2. **Access the app:**
   ```
   http://localhost:5000
   ```

3. **Login with test credentials:**
   - Username: your registered username
   - Password: your password

4. **Check the dashboard:**
   - Employee dashboard loads without errors ✅
   - Shows attendance data ✅
   - Shows working hours (0 for old records, actual hours for new) ✅
   - Shows attendance summary ✅

5. **Check console for confirmation:**
   ```
   ✅ Added working_hours column to attendance table
   ✅ Added status column to attendance table
   ✅ Database initialization complete
   ```

---

## Important Notes

✅ **Data Safety:**
- No data deleted
- No tables dropped
- All existing records preserved
- old records have working_hours = 0 by default

✅ **Backward Compatibility:**
- Old records work fine
- NULL values handled gracefully
- COALESCE returns defaults (0 for hours, 'Present' for status)

✅ **No Breaking Changes:**
- Login system unchanged
- Registration unchanged
- Admin credentials unchanged
- Dashboard layout unchanged

✅ **Future Attendance:**
- New check-ins will have proper working_hours
- Status will be set correctly
- All data captures properly

---

## Troubleshooting

### Issue: Dashboard still shows error
**Solution:**
1. Restart Flask app: `python app.py`
2. Run migration script: `python migrate_db.py`
3. Check error message in console
4. Verify `employee_database.db` file exists

### Issue: Some working_hours are 0
**Expected:** Old records (before fix) will have 0 by default. This is correct.
**New records** will calculate properly: check_out - check_in

### Issue: Status shows NULL
**Solution:** 
- Restart the app (COALESCE will return 'Present')
- Or run migration script

### Issue: Old attendance data disappeared
**This shouldn't happen** - verify:
1. Did you run `init_db()` (it should not delete data)
2. Check if database file still exists
3. Restore from backup if needed

---

## Files Modified

1. **app.py**
   - ✅ Updated `init_db()` function
   - ✅ Updated `calculate_attendance_summary()` function
   - ✅ Updated `employee_dashboard()` route
   - ✅ Updated `admin_dashboard()` route
   - ✅ Updated `get_attendance_history()` API endpoint

2. **migrate_db.py** (NEW)
   - ✅ Standalone migration utility
   - ✅ Safe, non-destructive
   - ✅ Provides detailed reporting

---

## When to Run

✅ **First Time:**
- Run `python app.py` - auto-migration happens
- Or run `python migrate_db.py` for detailed report

✅ **After Installing the Fixed Code:**
- Just start the app normally
- Auto-migration handles everything

✅ **To Verify Migration:**
- Run `python migrate_db.py` to see detailed schema report

---

## Summary

✅ **The Fix:**
- Non-destructive database migration
- Automatic on app startup
- Preserves all data
- Handles NULL values
- No breaking changes

✅ **Result:**
- Dashboard loads without errors
- Attendance data displays correctly
- Old records work with defaults
- New records calculate properly
- Login/registration unaffected

✅ **Status:** FIXED ✅

---

**Last Updated:** March 12, 2026
**Changes Made:** Database schema migration
**Data Safety:** Verified ✅
**Backward Compatibility:** Verified ✅
