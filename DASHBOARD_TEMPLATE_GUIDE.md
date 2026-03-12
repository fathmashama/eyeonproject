# Dashboard Template Integration Guide

## Overview
This guide shows how to display the new backend data in existing dashboard templates without changing the overall design.

---

## 1. TODAY'S ATTENDANCE CARD

### Data Available
```python
today_attendance = {
    'check_in': '09:15:30',      # Check-in time
    'check_out': '17:45:30',     # Check-out time  
    'working_hours': 8.5,        # Calculated hours
    'status': 'Present'          # Present/Absent
}
```

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-clock"></i> Today's Attendance
    </div>
    
    {% if today_attendance and today_attendance[1] %}
        <div class="info-row">
            <span class="info-label">Check-In</span>
            <span class="info-value">{{ today_attendance[1] }}</span>
        </div>
        
        <div class="info-row">
            <span class="info-label">Check-Out</span>
            <span class="info-value">{{ today_attendance[2] if today_attendance[2] else 'Not yet' }}</span>
        </div>
        
        <div class="info-row">
            <span class="info-label">Working Hours</span>
            <span class="info-value">{{ today_attendance[3] if today_attendance[3] else '-' }} hrs</span>
        </div>
        
        <div class="info-row">
            <span class="info-label">Status</span>
            <span class="badge badge-success">{{ today_attendance[4] }}</span>
        </div>
    {% else %}
        <div class="empty-state">
            <div class="empty-icon"><i class="fas fa-calendar-times"></i></div>
            <p>No attendance recorded today</p>
        </div>
    {% endif %}
</div>
```

---

## 2. ATTENDANCE SUMMARY CARD

### Data Available
```python
attendance_summary = {
    'total_days': 22,
    'present': 20,
    'absent': 2,
    'percentage': 90.91
}
```

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-chart-pie"></i> Attendance Summary
    </div>
    
    <div class="info-row">
        <span class="info-label">Total Days</span>
        <span class="info-value">{{ attendance_summary.total_days }}</span>
    </div>
    
    <div class="info-row">
        <span class="info-label">Present</span>
        <span class="info-value" style="color: #10b981;">{{ attendance_summary.present }}</span>
    </div>
    
    <div class="info-row">
        <span class="info-label">Absent</span>
        <span class="info-value" style="color: #ef4444;">{{ attendance_summary.absent }}</span>
    </div>
    
    <div class="info-row">
        <span class="info-label">Attendance %</span>
        <span class="info-value">{{ "%.2f" | format(attendance_summary.percentage) }}%</span>
    </div>
</div>
```

---

## 3. ATTENDANCE HISTORY TABLE

### Data Available
```python
attendance_history = [
    {
        'date': '2026-03-12',
        'check_in': '09:15:30',
        'check_out': '17:45:30',
        'working_hours': 8.5,
        'status': 'Present'
    },
    # ... more records
]
```

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-history"></i> Attendance History
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Check-In</th>
                    <th>Check-Out</th>
                    <th>Hours</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% if attendance_history %}
                    {% for record in attendance_history %}
                        <tr>
                            <td>{{ record[0] }}</td>
                            <td>{{ record[1] if record[1] else '-' }}</td>
                            <td>{{ record[2] if record[2] else '-' }}</td>
                            <td>{{ "%.2f" | format(record[3]) if record[3] else '-' }}</td>
                            <td>
                                <span class="badge badge-success">{{ record[4] }}</span>
                            </td>
                        </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="5" style="text-align: center; color: #999;">
                            No attendance records
                        </td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>
```

---

## 4. NOTIFICATIONS CARD

### Data Available
```python
notifications = [
    (1, 'System Maintenance', 'Down 2-4 PM today', '2026-03-12 10:30:00'),
    (2, 'Holiday', 'Tomorrow is a holiday', '2026-03-12 08:00:00'),
]
```

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-bell"></i> Notifications
    </div>
    
    {% if notifications %}
        {% for notif in notifications %}
            <div class="notification-item" style="padding: 1rem; border-bottom: 1px solid #eee; background: #f9fafb; margin-bottom: 0.75rem; border-radius: 0.5rem;">
                <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">
                    {{ notif[1] }}
                </div>
                <div style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.25rem;">
                    {{ notif[2] }}
                </div>
                <div style="font-size: 0.8rem; color: #9ca3af;">
                    {{ notif[3] }}
                </div>
            </div>
        {% endfor %}
    {% else %}
        <div class="empty-state">
            <div class="empty-icon"><i class="fas fa-bell-slash"></i></div>
            <p>No notifications yet</p>
        </div>
    {% endif %}
</div>
```

---

## 5. LEAVE REQUESTS CARD

### Data Available
```python
leave_requests = [
    (1, '2026-03-15', '2026-03-17', 'Medical appointment', 'pending'),
    (2, '2026-03-20', '2026-03-22', 'Personal', 'approved'),
]
```

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-calendar-alt"></i> Leave Requests
    </div>
    
    {% if leave_requests %}
        {% for leave in leave_requests %}
            <div class="leave-item">
                <div class="leave-dates">
                    {{ leave[1] }} to {{ leave[2] }}
                </div>
                <div class="leave-reason">
                    {{ leave[3] }}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge 
                        {% if leave[4] == 'pending' %}badge-pending{% elif leave[4] == 'approved' %}badge-success{% else %}badge-rejected{% endif %}">
                        {{ leave[4] | upper }}
                    </span>
                </div>
            </div>
        {% endfor %}
    {% else %}
        <div class="empty-state">
            <div class="empty-icon"><i class="fas fa-check-circle"></i></div>
            <p>No leave requests</p>
        </div>
    {% endif %}
</div>
```

---

## 6. ADMIN DASHBOARD - LEAVE REQUESTS TABLE

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-tasks"></i> Leave Requests
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Employee</th>
                    <th>From Date</th>
                    <th>To Date</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if leave_requests %}
                    {% for leave in leave_requests %}
                        <tr>
                            <td>{{ leave['name'] }}</td>
                            <td>{{ leave['from_date'] }}</td>
                            <td>{{ leave['to_date'] }}</td>
                            <td>{{ leave['reason'] }}</td>
                            <td>
                                <span class="badge 
                                    {% if leave['status'] == 'pending' %}badge-pending
                                    {% elif leave['status'] == 'approved' %}badge-success
                                    {% else %}badge-rejected{% endif %}">
                                    {{ leave['status'] | upper }}
                                </span>
                            </td>
                            <td>
                                {% if leave['status'] == 'pending' %}
                                    <form method="POST" action="/api/approve_leave/{{ leave['id'] }}" style="display: inline;">
                                        <button type="submit" class="btn-small" style="background: #10b981; color: white; padding: 0.4rem 0.8rem; border: none; border-radius: 0.3rem; cursor: pointer;">
                                            Approve
                                        </button>
                                    </form>
                                    <form method="POST" action="/api/reject_leave/{{ leave['id'] }}" style="display: inline;">
                                        <button type="submit" class="btn-small" style="background: #ef4444; color: white; padding: 0.4rem 0.8rem; border: none; border-radius: 0.3rem; cursor: pointer; margin-left: 0.5rem;">
                                            Reject
                                        </button>
                                    </form>
                                {% else %}
                                    <span style="color: #999;">-</span>
                                {% endif %}
                            </td>
                        </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="6" style="text-align: center; color: #999;">
                            No leave requests
                        </td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>
```

---

## 7. ADMIN DASHBOARD - NOTIFICATIONS MANAGEMENT

### Template Display
```html
<div class="card">
    <div class="card-title">
        <i class="fas fa-bell"></i> Create Notification
    </div>
    
    <form method="POST" action="/api/create_notification" style="margin-bottom: 2rem;">
        <div class="form-group">
            <label>Title</label>
            <input type="text" name="title" required style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 0.5rem;">
        </div>
        
        <div class="form-group">
            <label>Message</label>
            <textarea name="message" required style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 0.5rem; height: 100px;"></textarea>
        </div>
        
        <button type="submit" style="background: #2563eb; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: 600;">
            Create Notification
        </button>
    </form>
</div>

<div class="card">
    <div class="card-title">
        <i class="fas fa-inbox"></i> Notifications
    </div>
    
    {% if notifications %}
        {% for notif in notifications %}
            <div style="padding: 1rem; border-bottom: 1px solid #eee; background: #f9fafb; margin-bottom: 0.75rem; border-radius: 0.5rem;">
                <div style="font-weight: 600; color: #1f2937;">{{ notif[1] }}</div>
                <div style="color: #6b7280; margin: 0.5rem 0;">{{ notif[2] }}</div>
                <div style="font-size: 0.85rem; color: #9ca3af;">{{ notif[3] }}</div>
            </div>
        {% endfor %}
    {% else %}
        <div class="empty-state">
            <p>No notifications created yet</p>
        </div>
    {% endif %}
</div>
```

---

## 8. DATA INDEX REFERENCE

### attendance_history Tuple Indices
- `[0]` = date
- `[1]` = check_in
- `[2]` = check_out
- `[3]` = working_hours
- `[4]` = status

### notifications Tuple Indices
- `[0]` = id
- `[1]` = title
- `[2]` = message
- `[3]` = created_at

### leave_requests (Employee) Tuple Indices
- `[0]` = id
- `[1]` = from_date
- `[2]` = to_date
- `[3]` = reason
- `[4]` = status

### leave_requests (Admin) Dict Keys
- `['id']` = leave ID
- `['name']` = employee name
- `['from_date']` = start date
- `['to_date']` = end date
- `['reason']` = leave reason
- `['status']` = pending/approved/rejected

---

## 9. CSS CLASSES AVAILABLE

```css
.badge-success     /* Green - Approved/Present */
.badge-pending     /* Yellow - Pending */
.badge-rejected    /* Red - Rejected */
.empty-state       /* Empty message container */
.leave-item        /* Leave request styling */
.table-container   /* Table with scroll */
.info-row          /* Key-value pair row */
.info-label        /* Label text */
.info-value        /* Value text */
```

---

## 10. QUICK TEMPLATE SNIPPETS

### Show Status with Color
```html
<span class="badge 
    {% if item.status == 'Present' %}badge-success
    {% elif item.status == 'pending' %}badge-pending
    {% else %}badge-rejected{% endif %}">
    {{ item.status }}
</span>
```

### Format Time
```html
{{ time | default('-') }}
```

### Format Hours
```html
{{ "%.2f" | format(hours) if hours else '-' }} hrs
```

### Conditional Display
```html
{% if value %}
    {{ value }}
{% else %}
    <span style="color: #999;">-</span>
{% endif %}
```

---

## 11. RESPONSIVE CONSIDERATIONS

- All cards are already responsive (from original design)
- Tables use horizontal scroll on mobile
- No additional CSS needed for new data
- Existing grid layout handles new cards automatically

---

## 12. IMPORTANT NOTES FOR TEMPLATE UPDATES

✅ **Do:**
- Use existing CSS classes
- Keep the same card styling
- Use existing color variables
- Maintain responsive layout
- Keep the same navbar and structure

❌ **Don't:**
- Change overall design/layout
- Add new CSS stylesheets
- Modify existing routes
- Change authentication logic
- Remove any existing features

---

## 13. VERIFICATION CHECKLIST

After displaying data in templates:

- [ ] Today's attendance shows check-in/out times
- [ ] Attendance summary displays all 4 statistics
- [ ] Attendance history table shows all records
- [ ] Notifications display correctly
- [ ] Leave requests show status with colors
- [ ] Admin can see all employees' records
- [ ] Admin leave requests show approve/reject buttons
- [ ] Approve/reject buttons work
- [ ] Create notification form works
- [ ] All data updates in real-time
- [ ] No styling issues
- [ ] Mobile responsive

---

**No UI design changes needed - just add data display to existing templates!**
