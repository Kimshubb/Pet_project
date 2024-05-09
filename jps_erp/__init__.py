"""Start our flask app"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

"""Create an instance of the Flask class"""
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jpserp_kisii.db'
app.config ['SECRET_KEY'] = 'jps_erp'
db = SQLAlchemy(app)  
bcrypt = Bcrypt(app)

app.config['LOGIN_URL'] = '/sign_in'
login_manager = LoginManager(app)

from jps_erp.models import User
 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from jps_erp import routes