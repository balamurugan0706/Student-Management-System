from flask import Flask
from models import init_db, User, Course
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

with app.app_context():
    # Create Admin
    if not User.find_by_id("admin"):
        User.create_user("admin", "admin123", "admin", "System Administrator")
        print("Admin user created: admin / admin123")
    else:
        print("Admin user already exists.")

    # Create a test Instructor
    if not User.find_by_id("I501"):
        User.create_user("I501", "pass123", "instructor", "Dr. Smith")
        print("Instructor user created: I501 / pass123")

    # Create a test Student
    if not User.find_by_id("S101"):
        User.create_user("S101", "pass123", "student", "John Doe")
        print("Student user created: S101 / pass123")

    # Create initial courses with assigned instructors
    courses = [
        {"id": "CS101", "name": "Computer Science", "credits": 4, "instructor_id": "I501"},
        {"id": "CS102", "name": "Data Structures", "credits": 3, "instructor_id": "I501"},
        {"id": "CS103", "name": "Web Development", "credits": 3, "instructor_id": "I502"}
    ]
    
    from models import mongo
    for c in courses:
        if not mongo.db.courses.find_one({"course_id": c['id']}):
            mongo.db.courses.insert_one({
                "course_id": c['id'],
                "course_name": c['name'],
                "credits": c['credits'],
                "instructor_id": c['instructor_id']
            })
            print(f"Course created: {c['name']}")

    # Add Academic Details for student S101
    academic_data = [
        {"course_id": "CS101", "grade": "A", "attendance": 95},
        {"course_id": "CS102", "grade": "B+", "attendance": 88},
        {"course_id": "CS103", "grade": "A+", "attendance": 100}
    ]

    for data in academic_data:
        # Update grades
        mongo.db.grades.update_one(
            {"student_id": "S101", "course_id": data['course_id']},
            {"$set": {"grade": data['grade']}},
            upsert=True
        )
        # Update attendance
        mongo.db.attendance.update_one(
            {"student_id": "S101", "course_id": data['course_id']},
            {"$set": {"percentage": data['attendance']}},
            upsert=True
        )
    print("Populated academic records for S101.")
