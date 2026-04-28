from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt

mongo = PyMongo()
bcrypt = Bcrypt()

def init_db(app):
    mongo.init_app(app)
    bcrypt.init_app(app)

class User:
    @staticmethod
    def create_user(user_id, password, role, name=None, semester=None):
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            "user_id": user_id,
            "password": hashed_password,
            "role": role, # 'student', 'instructor', 'admin'
            "name": name
        }
        if role == 'student' and semester:
            user_data['semester'] = int(semester)
        return mongo.db.users.insert_one(user_data)

    @staticmethod
    def find_by_id(user_id):
        return mongo.db.users.find_one({"user_id": user_id})

    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.check_password_hash(stored_hash, password)

class Course:
    @staticmethod
    def create_course(course_id, name, credits):
        course_data = {
            "course_id": course_id,
            "course_name": name,
            "credits": credits
        }
        return mongo.db.courses.insert_one(course_data)

    @staticmethod
    def get_all():
        return list(mongo.db.courses.find())

class AuditLog:
    @staticmethod
    def log_activity(user_id, activity, status, ip_address=None):
        import datetime
        log_data = {
            "user_id": user_id,
            "activity": activity,
            "status": status,
            "ip": ip_address,
            "timestamp": datetime.datetime.utcnow()
        }
        mongo.db.audit_logs.insert_one(log_data)
