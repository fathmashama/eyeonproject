# EyeOn - Employee Attendance Dashboard

A professional, web-based employee attendance management system with real-time check-in/check-out, leave management, and comprehensive attendance tracking.

## Features

### For Employees
- 👤 **Professional Dashboard** - Modern, responsive UI with beautiful gradient design
- ✅ **Check-In/Check-Out** - Quick time tracking with one-click buttons
- 📊 **Attendance Summary** - View 90-day attendance statistics with percentage
- 📝 **Attendance History** - Detailed table of all attendance records
- 🗓️ **Leave Management** - Request leaves with date range and reason
- 🔔 **Notifications** - Real-time notifications and updates
- 👥 **Profile Information** - View employee details (ID, Department, Email)

### For Admin
- 🎯 **Employee Management** - Register and manage employees
- 📈 **Attendance Dashboard** - Real-time attendance overview
- 👨‍💼 **Leave Approval** - Approve or reject leave requests

## Tech Stack

- **Backend**: Flask (Python 3)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Font Awesome 6.4.0

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone/Navigate to project directory**
   ```bash
   cd c:\Users\aysha\Desktop\eyeonproject
   ```

2. **Install dependencies**
   ```bash
   pip install flask
   ```

3. **Initialize the database**
   ```bash
   python init_db.py
   ```
   This will:
   - Create the SQLite database
   - Create all required tables
   - Load employee data from `employee_info.csv`
   - Generate test credentials

4. **Start the Flask application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - You'll see the employee login page

## Default Test Credentials

### Employee Login
```
Username: ayshathnafiakm03
Password: 2023B144
```

Or use any of the other employees from the CSV file:
- Username: first part of email address
- Password: Employee ID

### Admin Login
```
Username: admin
Password: admin123
```

## Database Schema

### employees
- `id` - Primary key
- `employee_id` - Unique employee ID
- `name` - Employee name
- `email` - Email address
- `department` - Department
- `username` - Login username
- `password` - Login password

### attendance
- `id` - Primary key
- `employee_id` - Foreign key to employees
- `date` - Date of attendance
- `check_in` - Check-in time (HH:MM:SS)
- `check_out` - Check-out time (HH:MM:SS)
- `status` - Attendance status (present/absent)

### leave_requests
- `id` - Primary key
- `employee_id` - Foreign key to employees
- `start_date` - Leave start date
- `end_date` - Leave end date
- `reason` - Reason for leave
- `status` - Request status (pending/approved/rejected)

### notifications
- `id` - Primary key
- `employee_id` - Foreign key to employees
- `message` - Notification message
- `type` - Notification type (info/warning/success)
- `read` - Read status (0/1)

## API Endpoints

### Authentication
- `GET /` - Home/Login page
- `POST /employee_login` - Employee login
- `GET /employee_logout` - Employee logout

### Employee Dashboard
- `GET /employee_dashboard` - Main dashboard (requires login)

### Attendance
- `POST /api/check_in` - Record check-in time
- `POST /api/check_out` - Record check-out time
- `GET /api/employee_data` - Get employee profile data

### Leave Management
- `POST /api/leave_request` - Submit leave request

## Features in Detail

### Dashboard Sections

1. **Welcome Section**
   - Personalized greeting with current date
   - Motivational message

2. **Profile Information**
   - Employee ID
   - Department
   - Email address

3. **Today's Attendance**
   - Check-in status
   - Check-in time
   - Check-out time (if checked out)
   - Current status badge
   - Quick Check-In/Check-Out buttons

4. **Attendance Summary (Last 90 Days)**
   - Total working days
   - Present days count
   - Absent days count
   - Attendance percentage

5. **Attendance History**
   - Table showing last 10 attendance records
   - Date, Check-in time, Check-out time, Status
   - Color-coded status badges

6. **Leave Management**
   - View recent leave requests
   - Request new leave with modal form
   - Status indicators (Pending/Approved/Rejected)

7. **Notifications**
   - Real-time notifications
   - System updates
   - Important messages

## Design Features

- **Modern UI** - Gradient backgrounds with professional color scheme
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Smooth Animations** - Hover effects and transitions
- **Color Scheme**:
  - Primary: #2563eb (Blue)
  - Success: #10b981 (Green)
  - Danger: #ef4444 (Red)
  - Warning: #f59e0b (Amber)

## File Structure

```
eyeonproject/
├── app.py                          # Main Flask application
├── init_db.py                      # Database initialization script
├── employee_info.csv               # Employee data
├── attendance.csv                  # Attendance records backup
├── employee_dashboard.db           # SQLite database
├── static/
│   └── style.css                   # Global CSS styles
├── templates/
│   ├── employee_login.html         # Login page
│   ├── employee_dashboard.html     # Main dashboard
│   ├── admin_login.html            # Admin login
│   ├── admin_dashboard.html        # Admin dashboard
│   └── register.html               # Registration page
└── FaceDataSheet/                  # Face recognition data
```

## Future Enhancements

- [ ] Email notifications for leave approvals
- [ ] Biometric/Face recognition attendance
- [ ] Mobile app version
- [ ] Advanced reporting and analytics
- [ ] Department-wise attendance reports
- [ ] Shift management
- [ ] Holiday calendar
- [ ] Work-from-home tracking

## Security Considerations

⚠️ **Note**: This is a demo application. For production use:
- Use hashed passwords (bcrypt/werkzeug.security)
- Implement proper session management
- Add CSRF protection
- Use HTTPS
- Implement role-based access control (RBAC)
- Add input validation and sanitization
- Use environment variables for sensitive data

## Troubleshooting

### Port 5000 already in use
```bash
# Change port in app.py:
app.run(debug=True, port=5001)
```

### Database not initializing
```bash
# Delete existing database and reinitialize
rm employee_dashboard.db
python init_db.py
```

### CSS/Static files not loading
- Ensure you're in the correct project directory
- Restart the Flask app
- Clear browser cache (Ctrl+Shift+Delete)

## License

This project is provided as-is for educational and professional use.

## Support

For issues or questions, please refer to the code comments or contact the development team.

---

**Last Updated**: March 2026
**Version**: 1.0.0
