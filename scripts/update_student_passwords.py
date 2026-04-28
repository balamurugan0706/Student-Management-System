from flask import Flask
from models import init_db, mongo, bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

with app.app_context():
    # Hash the new password
    new_password = "stud@2026"
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    # Update all students
    result = mongo.db.users.update_many(
        {"role": "student"},
        {"$set": {"password": hashed_password}}
    )
    
    print(f"Successfully updated passwords for {result.modified_count} students.")
    print(f"New password for all students: {new_password}")
