from flask import Flask, session, redirect, url_for, request
from config import Config
from models import init_db, mongo, AuditLog
from routes import auth_bp, instructor_bp, admin_bp, student_bp
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    init_db(app)

    # Session management
    Session(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.errorhandler(404)
    def page_not_found(e):
        return "404 - Page Not Found", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "500 - Internal Server Error", 500

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            return redirect(url_for(f'{role}_bp.dashboard'))
        return redirect(url_for('auth_bp.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
