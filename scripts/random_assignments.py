from flask import Flask
from models import init_db, mongo
from config import Config
import random

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

with app.app_context():
    students = list(mongo.db.users.find({"role": "student"}))
    courses = list(mongo.db.courses.find())
    
    if not courses:
        print("No courses found. Please add courses first.")
        exit()

    grades_list = ["O", "A+", "A", "B+", "B", "C", "P", "F"]
    
    total_assignments = 0
    for student in students:
        student_id = student['user_id']
        
        # Pick 2 to 4 random courses for each student
        selected_courses = random.sample(courses, random.randint(2, min(4, len(courses))))
        
        for course in selected_courses:
            course_id = course['course_id']
            
            # Check if already enrolled
            if not mongo.db.grades.find_one({"student_id": student_id, "course_id": course_id}):
                # Add grade record
                mongo.db.grades.insert_one({
                    "student_id": student_id,
                    "course_id": course_id,
                    "grade": random.choice(grades_list)
                })
                
                # Add attendance record
                mongo.db.attendance.insert_one({
                    "student_id": student_id,
                    "course_id": course_id,
                    "percentage": random.randint(65, 100)
                })
                total_assignments += 1
                print(f"Assigned {student_id} to {course_id}")

    print(f"\nSuccessfully created {total_assignments} random course assignments.")
