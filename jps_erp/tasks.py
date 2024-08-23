from flask_mail import Message
from celery import Celery
from flask import current_app
from celery import current_task

celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery.task
def send_async_email_task(subject, recipient, body):
    """Celery task to send emails asynchronously."""
    with current_app.app_context():
        mail = current_app.extensions['mail']  # Use the global mail instance
        msg = Message(subject, recipients=[recipient], body=body)
        mail.send(msg)

def send_async_email(subject, recipient, body):
    """Function to enqueue email sending task."""
    send_async_email_task.delay(subject, recipient, body)

@celery.task
def log_to_syslog(message, level='info'):
    """Celery task to log messages to syslog."""
    app = current_task.get_app()
    with app.app_context():
        if level == 'info':
            app.logger.info(message)
        elif level == 'warning':
            app.logger.warning(message)
        elif level == 'error':
            app.logger.error(message)
        else:
            app.logger.debug(message)
