from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from flask_migrate import Migrate
from celery import Celery
from flask_session import Session
from flask_mail import Mail
import logging
import logging.handlers
import platform
import redis

# Initialize SQLAlchemy, Migrate, LoginManager, Mail
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# Setup logging
def setup_syslog_logger(app):
    if platform.system() == 'Linux':
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        syslog_handler.setFormatter(formatter)
        app.logger.addHandler(syslog_handler)
    elif platform.system() == 'Windows':
        event_log_handler = logging.handlers.NTEventLogHandler(app.name)
        event_log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        event_log_handler.setFormatter(formatter)
        app.logger.addHandler(event_log_handler)
    else:
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    
    # Initialize Redis-based session management
    Session(app)

    # Setup syslog logging
    setup_syslog_logger(app)

    # Register blueprints
    from jps_erp.auth import auth_bp
    from jps_erp.main import main_bp
    from jps_erp.students import students_bp
    from jps_erp.payments import payments_bp
    from jps_erp.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(settings_bp)

    return app

def create_celery_app(app=None):
    app = app or create_app()
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    
    # Bind the app context to Celery tasks
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
