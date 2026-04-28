from flask import Flask
from models import init_db, mongo
from config import Config
import random

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

programmes = ["B.E. Computer Science", "B.Tech Information Technology", "B.E. Electronics", "B.E. Mechanical"]
departments = ["CSE", "IT", "ECE", "MECH"]
academic_statuses = ["Regular", "Lateral Entry", "Transfer"]
admission_types = ["Merit", "Management", "Quota"]
sections = ["A", "B", "C"]
quotas = ["General", "OBC", "SC/ST", "EWS"]

with app.app_context():
    users = list(mongo.db.users.find())
    
    updated_count = 0
    for user in users:
        user_id = user['user_id']
        update_data = {}
        
        if user['role'] == 'student':
            update_data = {
                "application_number": f"APP2026{random.randint(1000, 9999)}",
                "email": f"{user_id.lower()}@edustream.edu",
                "phone": f"98765{random.randint(10000, 99999)}",
                "programme": random.choice(programmes),
                "department": random.choice(departments),
                "batch_year": f"2022-{random.randint(2025, 2026)}",
                "academic_status": random.choice(academic_statuses),
                "admission_type": random.choice(admission_types),
                "expected_pass_year": random.randint(2025, 2027),
                "section": random.choice(sections),
                "quota": random.choice(quotas)
            }
        elif user['role'] == 'instructor':
            update_data = {
                "email": f"{user_id.lower()}@edustream.edu",
                "phone": f"91234{random.randint(10000, 99999)}",
                "department": random.choice(departments),
                "designation": random.choice(["Professor", "Assistant Professor", "HOD"]),
                "employment_type": "Full-time"
            }
            
        if update_data:
            mongo.db.users.update_one({"user_id": user_id}, {"$set": update_data})
            updated_count += 1
            print(f"Updated info for: {user_id}")

    print(f"\nSuccessfully filled information for {updated_count} users.")
