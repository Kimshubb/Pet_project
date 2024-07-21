"""Start our flask app"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

# Create a directory for log files if it doesn't exist
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                        RotatingFileHandler(os.path.join(log_directory, 'app.log'), maxBytes=10240, backupCount=10)
                    ])

logging.debug("Logging setup complete.")

"""Create an instance of the Flask class"""
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, Audit, MpesaTransaction

# Uncomment and configure the user loader as needed
"""
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
"""

from jps_erp import routes

if __name__ == '__main__':
    app.run(debug=True)
