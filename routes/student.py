from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from .auth import login_required
from models import mongo, bcrypt
from utils.gpa_calc import calculate_gpa
import datetime

student_bp = Blueprint('student_bp', __name__)

@student_bp.route('/dashboard')
@login_required(role='student')
def dashboard():
    student_id = session['user_id']
    
    # Aggregation to get grades and course info
    pipeline = [
        {"$match": {"student_id": student_id}},
        {
            "$lookup": {
                "from": "courses",
                "localField": "course_id",
                "foreignField": "course_id",
                "as": "course_detail"
            }
        },
        {"$unwind": "$course_detail"}
    ]
    
    grades = list(mongo.db.grades.aggregate(pipeline))
    attendance_docs = list(mongo.db.attendance.find({"student_id": student_id}))
    
    # Calculate GPA
    gpa = calculate_gpa(grades)
    
    # Calculate Average Attendance
    if attendance_docs:
        total_att = sum(float(doc.get('percentage', 0)) for doc in attendance_docs)
        avg_attendance = round(total_att / len(attendance_docs), 2)
    else:
        avg_attendance = 0.0
    
    # Add attendance to grade items for display
    att_map = {doc['course_id']: doc.get('percentage', 0) for doc in attendance_docs}
    for g in grades:
        g['attendance'] = att_map.get(g['course_id'], '--')
    
    user = mongo.db.users.find_one({"user_id": student_id})
    semester = user.get('semester', '--') if user else '--'
    
    return render_template('student/dashboard.html', grades=grades, gpa=gpa, attendance=avg_attendance, semester=semester)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required(role='student')
def profile():
    student_id = session['user_id']
    user = mongo.db.users.find_one({"user_id": student_id})
    return render_template('student/profile.html', user=user)

@student_bp.route('/change-password', methods=['POST'])
@login_required(role='student')
def change_password():
    student_id = session['user_id']
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash("Passwords do not match!", "error")
        return redirect(url_for('student_bp.profile'))
    
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    mongo.db.users.update_one(
        {"user_id": student_id},
        {"$set": {"password": hashed_password}}
    )
    flash("Password updated successfully!", "success")
    return redirect(url_for('student_bp.profile'))

@student_bp.route('/support/submit', methods=['POST'])
@login_required(role='student')
def submit_query():
    student_id = session['user_id']
    subject = request.form.get('subject')
    message = request.form.get('message')
    from datetime import datetime
    mongo.db.support_queries.insert_one({
        "student_id": student_id,
        "subject": subject,
        "message": message,
        "status": "Pending",
        "date": datetime.now()
    })
    flash("Query submitted successfully!", "success")
    return redirect(url_for('student_bp.dashboard'))
