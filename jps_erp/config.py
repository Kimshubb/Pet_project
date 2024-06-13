import os 
basedir = os.path.abspath(os.path.dirname(__file__))    # get the directory of the current file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jps_erp'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
    'sqlite:///' + os.path.join(basedir, 'jpserp_kisii.db')

    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
    MPESA_INITIATOR_NAME = os.getenv('MPESA_INITIATOR_NAME')
    MPESA_SECURITY_CREDENTIAL = os.getenv('MPESA_SECURITY_CREDENTIAL')
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
    MPESA_RESULT_URL = os.getenv('MPESA_RESULT_URL')
    MPESA_QUEUE_TIMEOUT_URL = os.getenv('MPESA_QUEUE_TIMEOUT_URL')
