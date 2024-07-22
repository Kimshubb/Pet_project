import os

basedir = os.path.abspath(os.path.dirname(__file__))  # Get the directory of the current file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'mysql://myuser:mypassword@localhost/mydatabase'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # To suppress a warning
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    ALLOWED_EXTENSIONS = {'pdf'}

