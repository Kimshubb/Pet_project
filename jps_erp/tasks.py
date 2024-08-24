from flask_mail import Message
from celery import Celery
from flask import current_app
from celery import current_task
from jps_erp.sms_service import SMSService

celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery.task
def send_payment_notification(mobile, message):
    """Send SMS notification to a single parent after payment."""
    sms_service = SMSService(current_app.config['ADVANTA_API_KEY'], current_app.config['ADVANTA_PARTNER_ID'])
    sms_service.send_single_sms(mobile, message, current_app.config['ADVANTA_SHORTCODE'])

@celery.task
def send_bulk_sms_notification(sms_list):
    """Send bulk SMS notifications to parents."""
    sms_service = SMSService(current_app.config['ADVANTA_API_KEY'], current_app.config['ADVANTA_PARTNER_ID'])
    sms_service.send_bulk_sms(sms_list)
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

@celery.task
def log_auth_event(username, event_type, success=True):
    """Celery task to log authentication events."""
    app = current_task.get_app()
    with app.app_context():
        if success:
            message = f"User '{username}' {event_type} successful."
            app.logger.info(message)
        else:
            message = f"User '{username}' {event_type} failed."
            app.logger.warning(message)

@celery.task
def log_user_registration(username):
    """Celery task to log user registration."""
    app = current_task.get_app()
    with app.app_context():
        message = f"New user registration: {username}"
        app.logger.info(message)


@celery.task
def log_payment_event(student_id, amount, success=True, transaction_id=None):
    """Celery task to log payment processing events."""
    app = current_task.get_app()
    with app.app_context():
        if success:
            message = f"Payment of {amount} for student {student_id} successful. Transaction ID: {transaction_id}"
            app.logger.info(message)
        else:
            message = f"Payment of {amount} for student {student_id} failed."
            app.logger.error(message)

@celery.task
def log_sms_event(phone_number, message, success=True, bulk=False):
    """Celery task to log SMS notification events."""
    app = current_task.get_app()
    with app.app_context():
        if success:
            if bulk:
                message = f"Bulk SMS sent successfully to {phone_number}"
            else:
                message = f"SMS sent successfully to {phone_number}"
            app.logger.info(message)
        else:
            message = f"Failed to send SMS to {phone_number}"
            app.logger.error(message)

@celery.task
def log_external_service_event(service_name, action, success=True, details=None):
    """Celery task to log external service interactions."""
    app = current_task.get_app()
    with app.app_context():
        if success:
            message = f"External service '{service_name}' {action} successful. Details: {details}"
            app.logger.info(message)
        else:
            message = f"External service '{service_name}' {action} failed. Details: {details}"
            app.logger.error(message)

@celery.task
def log_error_event(error_message, exception_details=None):
    """Celery task to log errors and exceptions."""
    app = current_task.get_app()
    with app.app_context():
        if exception_details:
            message = f"Error occurred: {error_message}. Exception details: {exception_details}"
        else:
            message = f"Error occurred: {error_message}"
        app.logger.error(message)



