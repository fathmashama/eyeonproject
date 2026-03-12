"""
Database Migration Utility for EyeOn Attendance System
This script safely adds missing columns to existing attendance table
"""

import sqlite3
import os

DB_PATH = "employee_database.db"

def migrate_attendance_table():
    """Safely add missing columns to attendance table"""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found. It will be created on app startup.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🔍 Checking attendance table structure...")
    
    # Get current columns
    c.execute("PRAGMA table_info(attendance)")
    existing_columns = {row[1]: row for row in c.fetchall()}
    
    print(f"✅ Found {len(existing_columns)} columns in attendance table")
    for col_name in existing_columns:
        print(f"   - {col_name}")
    
    # Check and add missing columns
    missing_columns = {
        'working_hours': 'REAL DEFAULT 0',
        'status': "TEXT DEFAULT 'Present'"
    }
    
    for col_name, col_def in missing_columns.items():
        if col_name not in existing_columns:
            try:
                print(f"\n🔧 Adding missing column: {col_name}")
                c.execute(f"ALTER TABLE attendance ADD COLUMN {col_name} {col_def}")
                print(f"✅ Successfully added {col_name} column")
            except Exception as e:
                print(f"⚠️  Error adding {col_name}: {str(e)}")
        else:
            print(f"✅ Column {col_name} already exists")
    
    conn.commit()
    
    # Verify migration
    print("\n🔍 Verifying final structure...")
    c.execute("PRAGMA table_info(attendance)")
    final_columns = [row[1] for row in c.fetchall()]
    
    print(f"✅ Final attendance table has {len(final_columns)} columns:")
    for col in final_columns:
        print(f"   - {col}")
    
    # Check for data integrity
    c.execute("SELECT COUNT(*) FROM attendance")
    record_count = c.fetchone()[0]
    print(f"\n✅ Attendance table contains {record_count} records (preserved)")
    
    # Check for NULL values
    c.execute("SELECT COUNT(*) FROM attendance WHERE working_hours IS NULL")
    null_working_hours = c.fetchone()[0]
    if null_working_hours > 0:
        print(f"⚠️  {null_working_hours} records have NULL working_hours (will default to 0)")
    
    c.execute("SELECT COUNT(*) FROM attendance WHERE status IS NULL")
    null_status = c.fetchone()[0]
    if null_status > 0:
        print(f"⚠️  {null_status} records have NULL status (will default to 'Present')")
    
    conn.close()
    print("\n✅ Database migration complete!")

if __name__ == "__main__":
    migrate_attendance_table()
