# EduStream Student Management System

A robust, role-based academic management platform built with Python (Flask) and MongoDB.

## Features

- **Role-Based Access Control (RBAC)**: Distinct dashboards for Students, Instructors, and Administrators.
- **Bulk Data Management**: Instructors can upload student records via CSV.
- **Academic Tracking**: Comprehensive GPA calculation and attendance monitoring.
- **Security**: Password hashing with Bcrypt and audit logging for sensitive actions.
- **Premium UI**: Modern dark-mode interface with glassmorphism and smooth animations.

## Tech Stack

- **Backend**: Flask
- **Database**: MongoDB (PyMongo)
- **Frontend**: HTML5, Vanilla CSS, JS
- **Security**: Flask-Bcrypt, Flask-Session

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file from the template and provide your `MONGO_URI`.

3. **Initialize Database**:
   ```bash
   python scripts/seed_db.py
   ```

4. **Run Application**:
   ```bash
   python app.py
   ```

## Default Credentials

- **Admin**: `admin` / `admin123`
- **Instructor**: `I501` / `pass123`
- **Student**: `S101` / `pass123`

## API & Schema Documentation

### MongoDB Collections
- `users`: Stores account information (User ID, Hashed Password, Role, Name).
- `courses`: Master course list (ID, Name, Credits).
- `grades`: Student performance records (Student ID, Course ID, Letter Grade).
- `attendance`: Raw attendance data.
- `audit_logs`: Tracking of login attempts and administrative actions.
- `support_queries`: Contact queries from students.
