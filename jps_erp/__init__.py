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
from dotenv import load_dotenv

# Initialize SQLAlchemy, Migrate, LoginManager, Mail
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()


# Setup logging
def setup_syslog_logger(app):
    log_level = logging.INFO
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    if platform.system() == 'Linux':
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_handler.setLevel(log_level)
        syslog_handler.setFormatter(formatter)
        app.logger.addHandler(syslog_handler)
        app.logger.info('Logging initialized on Linux')
    elif platform.system() == 'Windows':
        event_log_handler = logging.handlers.NTEventLogHandler(app.name)
        event_log_handler.setLevel(log_level)
        event_log_handler.setFormatter(formatter)
        app.logger.addHandler(event_log_handler)
        app.logger.info('Logging initialized on Windows')
    else:
        log_file = 'jps_erp.log'
        file_handler = logging.handlers.RotatingFileHandler(log_file , maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        app.logger.info('Logging initialized on %s', platform.system())
    app.logger.propagate = False

def create_app():
    app = Flask(__name__)
    #load env variables from .env file
    load_dotenv()
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

    from jps_erp.commands import register_commands
    register_commands(app)

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
