"""Start our flask app"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from flask_migrate import Migrate


"""Create an instance of the Flask class"""
app = Flask(__name__)
app.config.from_object('jps_erp.config.Config')
db = SQLAlchemy(app)
migrate = Migrate(app, db) 

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, Audit, MpesaTransaction 
"""
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
"""
from jps_erp import routes