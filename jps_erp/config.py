import os 
basedir = os.path.abspath(os.path.dirname(__file__))    # get the directory of the current file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jps_erp'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
    'sqlite:///' + os.path.join(basedir, 'jpserp_kisii.db')