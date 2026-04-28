import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import init_db, User, mongo, bcrypt
from config import Config

# New stronger passwords (not in breach databases)
ADMIN_PASSWORD    = 'Admin@SDMS#2026'
INST_PASSWORD     = 'Instr@SDMS#2026'
STUDENT_PASSWORD  = 'Stud@SDMS#2026'

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

with app.app_context():
    admin_hash = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
    result_admin = mongo.db.users.update_one(
        {'user_id': 'admin'},
        {'$set': {'password': admin_hash}}
    )
    print(f"Admin    | ID: admin | Password: {ADMIN_PASSWORD} | Reset: {'OK' if result_admin.matched_count else 'NOT FOUND'}")

    inst_hash = bcrypt.generate_password_hash(INST_PASSWORD).decode('utf-8')
    stud_hash = bcrypt.generate_password_hash(STUDENT_PASSWORD).decode('utf-8')

    if not User.find_by_id('I501'):
        User.create_user('I501', INST_PASSWORD, 'instructor', 'Dr. Smith')
        print(f"Instructor | ID: I501 | Password: {INST_PASSWORD} | Created")
    else:
        mongo.db.users.update_one({'user_id': 'I501'}, {'$set': {'password': inst_hash}})
        print(f"Instructor | ID: I501 | Password: {INST_PASSWORD} | Reset: OK")

    if not User.find_by_id('S101'):
        User.create_user('S101', STUDENT_PASSWORD, 'student', 'John Doe')
        print(f"Student    | ID: S101 | Password: {STUDENT_PASSWORD} | Created")
    else:
        mongo.db.users.update_one({'user_id': 'S101'}, {'$set': {'password': stud_hash}})
        print(f"Student    | ID: S101 | Password: {STUDENT_PASSWORD} | Reset: OK")

    print("\nAll passwords updated successfully!")

    # Print all users
    users = list(mongo.db.users.find({}, {'user_id': 1, 'role': 1, 'name': 1, '_id': 0}))
    print("\n--- Users in Database ---")
    for u in users:
        print(f"  ID: {u.get('user_id')} | Role: {u.get('role')} | Name: {u.get('name')}")
    print("\nAll passwords have been reset successfully!")
