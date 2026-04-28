from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .auth import login_required
from models import mongo
from werkzeug.security import check_password_hash
import pandas as pd
import io

instructor_bp = Blueprint('instructor_bp', __name__)

@instructor_bp.route('/dashboard')
@login_required(role='instructor')
def dashboard():
    instructor_id = session['user_id']
    
    # Get courses taught by this instructor
    courses = list(mongo.db.courses.find({"instructor_id": instructor_id}))
    course_ids = [c['course_id'] for c in courses]
    
    # Get students enrolled in these courses
    # We join with 'users' for names and 'courses' for course names
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
        {"$unwind": "$student_detail"},
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
    
    student_records = list(mongo.db.grades.aggregate(pipeline))
    
    # Also get attendance for display
    attendance = list(mongo.db.attendance.find({"course_id": {"$in": course_ids}}))
    att_map = {(a['student_id'], a['course_id']): a.get('percentage', 0) for a in attendance}
    
    for s in student_records:
        s['attendance'] = att_map.get((s['student_id'], s['course_id']), '--')

    # Calculate Class Analytics
    analytics = {
        "avg_gpa": 0,
        "pass_rate": 0,
        "total_enrolled": len(student_records)
    }
    
    if student_records:
        from utils.gpa_calc import get_grade_points
        total_gp = sum(get_grade_points(s.get('grade', 'F')) for s in student_records)
        analytics['avg_gpa'] = round(total_gp / len(student_records), 2)
        
        passes = len([s for s in student_records if s.get('grade', 'F') != 'F'])
        analytics['pass_rate'] = round((passes / len(student_records)) * 100, 1)

    return render_template('instructor/dashboard.html', 
                           students=student_records, 
                           courses=courses, 
                           analytics=analytics)

@instructor_bp.route('/upload_csv', methods=['GET', 'POST'])
@login_required(role='instructor')
def upload_csv():
    if request.method == 'GET':
        return render_template('instructor/upload.html')
        
    if 'csv_file' not in request.files:
        flash("No file part", "error")
        return redirect(url_for('instructor_bp.dashboard'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash("No selected file", "error")
        return redirect(url_for('instructor_bp.dashboard'))

    try:
        # Read with UTF-8-sig to strip BOM, try comma first then semicolon/tab
        raw = file.stream.read()
        try:
            text = raw.decode('utf-8-sig')   # strips BOM if present
        except Exception:
            text = raw.decode('latin-1')

        df = pd.read_csv(io.StringIO(text))

        # Normalize column names: strip spaces, lowercase
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        required_cols = {'student_id', 'course_id', 'grade', 'attendance'}
        missing = required_cols - set(df.columns)
        if missing:
            flash(f"Invalid CSV. Missing columns: {missing}. Your columns: {list(df.columns)}", "error")
            return redirect(url_for('instructor_bp.upload_csv'))

        # Strip whitespace from string values
        for col in ['student_id', 'course_id', 'grade']:
            df[col] = df[col].astype(str).str.strip()

        updated = 0
        errors  = []
        for idx, row in df.iterrows():
            try:
                att_val = float(row['attendance'])
                mongo.db.grades.update_one(
                    {"student_id": row['student_id'], "course_id": row['course_id']},
                    {"$set": {"grade": row['grade']}},
                    upsert=True
                )
                mongo.db.attendance.update_one(
                    {"student_id": row['student_id'], "course_id": row['course_id']},
                    {"$set": {"percentage": att_val}},
                    upsert=True
                )
                updated += 1
            except Exception as row_err:
                errors.append(f"Row {idx+2}: {str(row_err)}")

        if errors:
            flash(f"Processed {updated} records with {len(errors)} error(s): {'; '.join(errors[:3])}", "error")
        else:
            flash(f"CSV uploaded successfully! {updated} student record(s) updated.", "success")

    except Exception as e:
        flash(f"Failed to read CSV: {str(e)}", "error")
        return redirect(url_for('instructor_bp.upload_csv'))

    return redirect(url_for('instructor_bp.dashboard'))

@instructor_bp.route('/download_sample_csv')
@login_required(role='instructor')
def download_sample_csv():
    from flask import Response
    sample = "student_id,course_id,grade,attendance\nS101,CS101,A+,95\nS102,CS101,B+,88\nS101,CS102,O,100\n"
    return Response(
        sample,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=sample_bulk_upload.csv"}
    )

@instructor_bp.route('/manage_student/<student_id>/<course_id>', methods=['GET', 'POST'])
@login_required(role='instructor')
def manage_student(student_id, course_id):
    instructor_id = session['user_id']
    
    # Verify instructor teaches this course
    course = mongo.db.courses.find_one({"course_id": course_id, "instructor_id": instructor_id})
    if not course:
        flash("Authorization Error: You do not teach this course.", "error")
        return redirect(url_for('instructor_bp.dashboard'))
        
    if request.method == 'POST':
        grade = request.form.get('grade')
        attendance = request.form.get('attendance')
        
        mongo.db.grades.update_one(
            {"student_id": student_id, "course_id": course_id},
            {"$set": {"grade": grade}},
            upsert=True
        )
        mongo.db.attendance.update_one(
            {"student_id": student_id, "course_id": course_id},
            {"$set": {"percentage": attendance}},
            upsert=True
        )
        flash(f"Updated records for {student_id}", "success")
        return redirect(url_for('instructor_bp.dashboard'))
        
    student = mongo.db.users.find_one({"user_id": student_id})
    grade_doc = mongo.db.grades.find_one({"student_id": student_id, "course_id": course_id})
    att_doc = mongo.db.attendance.find_one({"student_id": student_id, "course_id": course_id})
    
    return render_template('instructor/manage_student.html',
                           student=student,
                           course=course,
                           grade=grade_doc.get('grade') if grade_doc else '',
                           attendance=att_doc.get('percentage') if att_doc else '')

@instructor_bp.route('/profile')
@login_required(role='instructor')
def profile():
    instructor_id = session['user_id']
    user = mongo.db.users.find_one({"user_id": instructor_id})
    return render_template('instructor/profile.html', user=user)

@instructor_bp.route('/change-password', methods=['POST'])
@login_required(role='instructor')
def change_password():
    instructor_id = session['user_id']
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        flash("Passwords do not match!", "error")
        return redirect(url_for('instructor_bp.profile'))

    if len(new_password) < 6:
        flash("Password must be at least 6 characters!", "error")
        return redirect(url_for('instructor_bp.profile'))

    from models import bcrypt
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    mongo.db.users.update_one(
        {"user_id": instructor_id},
        {"$set": {"password": hashed_password}}
    )

    flash("Password updated successfully!", "success")
    return redirect(url_for('instructor_bp.profile'))
