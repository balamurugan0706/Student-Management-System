from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import User, AuditLog
from functools import wraps

auth_bp = Blueprint('auth_bp', __name__)

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth_bp.login'))
            if role and session.get('role') != role:
                flash("Access Denied: Unauthorized Role", "error")
                return redirect(url_for('auth_bp.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        user = User.find_by_id(user_id)
        
        if user and User.verify_password(user['password'], password):
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['name'] = user.get('name', 'User')
            
            AuditLog.log_activity(user_id, "Login", "Success", request.remote_addr)
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_bp.dashboard'))
            elif user['role'] == 'instructor':
                return redirect(url_for('instructor_bp.dashboard'))
            else:
                return redirect(url_for('student_bp.dashboard'))
        
        AuditLog.log_activity(user_id, "Login", "Failed", request.remote_addr)
        flash("Invalid credentials", "error")
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
