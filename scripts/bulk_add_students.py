from flask import Flask
from models import init_db, User, mongo
from config import Config
import random

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

student_names = [
    "Aravind Kumar", "Bhavana Reddy", "Chaitanya Varma", "Deepika Sharma", "Eshwar Rao",
    "Fathima Bi", "Ganesh Hegde", "Harish Iyer", "Indira Priyadarshini", "Jaya Prakash",
    "Karthik Raja", "Laxmi Narayan", "Manoj Bajpayee", "Nandini Gupta", "Omprakash Singh",
    "Priyanka Chopra", "Qasim Khan", "Rahul Dravid", "Sneha Lata", "Tarun Kumar",
    "Usha Rani", "Vijay Kumar", "Waseem Akram", "Xavier John", "Yogeshwar Dutt",
    "Zeenat Aman", "Aditya Birla", "Binny Bansal"
]

with app.app_context():
    # Get current student count to avoid ID collisions
    existing_students = list(mongo.db.users.find({"role": "student"}))
    start_id = 102 # Starting after S101
    
    added_count = 0
    for name in student_names:
        student_id = f"S{start_id}"
        if not User.find_by_id(student_id):
            semester = random.randint(1, 8)
            User.create_user(student_id, "pass123", "student", name, semester)
            print(f"Added student: {name} ({student_id}) - Sem {semester}")
            added_count += 1
        start_id += 1
        if added_count >= 25:
            break
            
    print(f"\nSuccessfully added {added_count} students to the database.")
