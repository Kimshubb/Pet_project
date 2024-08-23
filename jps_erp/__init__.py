from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from flask_migrate import Migrate
from celery import Celery
import redis
import os
from flask_session import Session
from flask_mail import Mail
import logging
import logging.handlers
import platform


# Initialize SQLAlchemy and Migrate
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# Setup logging
def setup_syslog_logger(app):
    if platform.system() == 'Linux':
        # Configure syslog handler for Linux
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        syslog_handler.setFormatter(formatter)
        app.logger.addHandler(syslog_handler)
    elif platform.system() == 'Windows':
        # Use NTEventLogHandler for Windows Event Logs
        event_log_handler = logging.handlers.NTEventLogHandler(app.name)
        event_log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        event_log_handler.setFormatter(formatter)
        app.logger.addHandler(event_log_handler)
    else:
        # Fallback to file-based logging
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery

def create_app():
    """Create an instance of the Flask class."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Initialize login manager
    login_manager.login_view = 'auth.login'
    

    # Initialize Celery
    celery = make_celery(app)

    # Redis client for caching
    redis_client = redis.StrictRedis.from_url(app.config['REDIS_URL'])
    #Config.init_app(app)
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

    #Initialize redis based session
    Session(app)


    # Return the app, celery instance, and redis client
    return app, celery, redis_client