from flask import Blueprint, render_template, request, flash, redirect, url_for
from .auth import login_required
from models import mongo, User, Course

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    stats = {
        "students": mongo.db.users.count_documents({"role": "student"}),
        "instructors": mongo.db.users.count_documents({"role": "instructor"}),
        "courses": mongo.db.courses.count_documents({})
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required(role='admin')
def manage_users():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        role = request.form.get('role')
        name = request.form.get('name')
        semester = request.form.get('semester')
        
        if User.find_by_id(user_id):
            flash("User ID already exists", "error")
        else:
            User.create_user(user_id, password, role, name, semester)
            flash("User created successfully", "success")
            
    users = list(mongo.db.users.find().sort("user_id", 1))
    return render_template('admin/users.html', users=users)

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required(role='admin')
def manage_courses():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        name = request.form.get('course_name')
        credits = request.form.get('credits')
        instructor_id = request.form.get('instructor_id')
        
        # Manually create so we can include instructor_id
        mongo.db.courses.insert_one({
            "course_id": course_id,
            "course_name": name,
            "credits": credits,
            "instructor_id": instructor_id
        })
        flash("Course added successfully", "success")
        
    courses = Course.get_all()
    students = list(mongo.db.users.find({"role": "student"}).sort("user_id", 1))
    instructors = list(mongo.db.users.find({"role": "instructor"}).sort("user_id", 1))
    return render_template('admin/courses.html', courses=courses, students=students, instructors=instructors)

@admin_bp.route('/logs')
@login_required(role='admin')
def view_logs():
    logs = list(mongo.db.audit_logs.find().sort("timestamp", -1).limit(100))
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/support')
@login_required(role='admin')
def manage_support():
    queries = list(mongo.db.support_queries.find().sort("timestamp", -1))
    return render_template('admin/support.html', queries=queries)

@admin_bp.route('/support/resolve/<query_id>', methods=['POST'])
@login_required(role='admin')
def resolve_query(query_id):
    from bson.objectid import ObjectId
    mongo.db.support_queries.update_one(
        {"_id": ObjectId(query_id)},
        {"$set": {"status": "Resolved"}}
    )
    flash("Query marked as resolved", "success")
    return redirect(url_for('admin_bp.manage_support'))

@admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_user(user_id):
    user = User.find_by_id(user_id)
    assigned_data = {}
    
    if user['role'] == 'instructor':
        # Get courses taught by this instructor
        courses = list(mongo.db.courses.find({"instructor_id": user_id}))
        course_ids = [c['course_id'] for c in courses]
        
        # Get students in those courses
        pipeline = [
            {"$match": {"course_id": {"$in": course_ids}}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "student_id",
                    "foreignField": "user_id",
                    "as": "student_detail"
                }
            },
            {"$unwind": "$student_detail"}
        ]
        students = list(mongo.db.grades.aggregate(pipeline))
        assigned_data = {"courses": courses, "students": students}

    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        
        update_data = {"name": name, "role": role}
        
        extra_fields = [
            'application_number', 'email', 'phone', 'programme', 'department', 
            'batch_year', 'academic_status', 'admission_type', 'expected_pass_year', 
            'expected_pass_date', 'section', 'quota', 'designation', 'employment_type'
        ]
        for field in extra_fields:
            val = request.form.get(field)
            if val is not None:
                update_data[field] = val

        if role == 'student':
            semester = request.form.get('semester')
            if semester:
                update_data['semester'] = int(semester)
                
        mongo.db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        flash("User updated successfully", "success")
        return redirect(url_for('admin_bp.manage_users'))
        
    return render_template('admin/edit_user.html', user=user, assigned_data=assigned_data)

@admin_bp.route('/courses/edit/<course_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_course(course_id):
    course = mongo.db.courses.find_one({"course_id": course_id})
    if request.method == 'POST':
        name = request.form.get('course_name')
        credits = request.form.get('credits')
        instructor = request.form.get('instructor_id')
        mongo.db.courses.update_one(
            {"course_id": course_id},
            {"$set": {"course_name": name, "credits": credits, "instructor_id": instructor}}
        )
        flash("Course updated successfully", "success")
        return redirect(url_for('admin_bp.manage_courses'))
        
    instructors = list(mongo.db.users.find({"role": "instructor"}))
    return render_template('admin/edit_course.html', course=course, instructors=instructors)

@admin_bp.route('/users/reset-password/<user_id>', methods=['POST'])
@login_required(role='admin')
def reset_user_password(user_id):
    from models import bcrypt
    new_password    = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if not new_password:
        flash("Password cannot be empty.", "error")
        return redirect(url_for('admin_bp.edit_user', user_id=user_id))

    if new_password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('admin_bp.edit_user', user_id=user_id))

    if len(new_password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for('admin_bp.edit_user', user_id=user_id))

    hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
    mongo.db.users.update_one(
        {"user_id": user_id},
        {"$set": {"password": hashed}}
    )
    flash(f"Password for {user_id} updated successfully.", "success")
    return redirect(url_for('admin_bp.edit_user', user_id=user_id))

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required(role='admin')
def delete_user(user_id):
    mongo.db.users.delete_one({"user_id": user_id})
    # Clean up related records
    mongo.db.grades.delete_many({"student_id": user_id})
    mongo.db.attendance.delete_many({"student_id": user_id})
    flash(f"User {user_id} deleted permanently", "success")
    return redirect(url_for('admin_bp.manage_users'))

@admin_bp.route('/courses/delete/<course_id>', methods=['POST'])
@login_required(role='admin')
def delete_course(course_id):
    mongo.db.courses.delete_one({"course_id": course_id})
    # Clean up enrollments
    mongo.db.grades.delete_many({"course_id": course_id})
    mongo.db.attendance.delete_many({"course_id": course_id})
    flash(f"Course {course_id} and all related enrollments deleted", "success")
    return redirect(url_for('admin_bp.manage_courses'))

@admin_bp.route('/enroll', methods=['POST'])
@login_required(role='admin')
def enroll_student():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    # Check if student exists
    if not User.find_by_id(student_id):
        flash("Student not found", "error")
        return redirect(url_for('admin_bp.manage_courses'))
        
    # Check if course exists
    if not mongo.db.courses.find_one({"course_id": course_id}):
        flash("Course not found", "error")
        return redirect(url_for('admin_bp.manage_courses'))
        
    # Create enrollment (Grade record with empty grade)
    mongo.db.grades.update_one(
        {"student_id": student_id, "course_id": course_id},
        {"$setOnInsert": {"grade": "F"}},
        upsert=True
    )
    # Create attendance record
    mongo.db.attendance.update_one(
        {"student_id": student_id, "course_id": course_id},
        {"$setOnInsert": {"percentage": 0}},
        upsert=True
    )
    flash(f"Student {student_id} enrolled in {course_id}", "success")
    return redirect(url_for('admin_bp.manage_courses'))
