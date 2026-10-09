# Student Profile Management System

A responsive, lightweight B.Tech CSE Mini Project built with Python Flask and SQLite, hosted on Render.

## Features
- **Authentication**: Secure Login / Logout with hashed passwords using Werkzeug.
- **Database**: Automatic SQLite table creation on application startup.
- **Dashboard**: Student profile view including Roll Number, Course, Semester, Attendance, and Academic Marks.
- **Responsive UI**: Modern glassmorphic and colourful mobile-friendly interface built with custom CSS.

## Demo Credentials
- **Email**: `student@gmail.com`
- **Password**: `Student@123`

## Directory Structure
```
student-portal/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── login.html
│   └── dashboard.html
└── static/
    └── style.css
```

## Render Deployment Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
