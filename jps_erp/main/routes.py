from . import main_bp
from flask import render_template, redirect, url_for, flash, session, jsonify, request
from jps_erp.models import Term, Stream, Grade, Student
from jps_erp.utils import current_year, get_recent_payments, active_students, inactive_students_term, inactive_students_year, paid_via_method_today
from flask_login import login_required, current_user
from jps_erp.tasks import send_bulk_sms_notification, log_to_syslog, log_error_event


@main_bp.route('/bulk_sms', methods=['POST', 'GET'])
@login_required
def send_bulk_sms_route():
    grades = Grade.query.filter_by(school_id=current_user.school_id).all()

    if request.method == 'POST':
        selected_grade = request.form.get('grade')
        message = request.form.get('message')

        students = Student.query.filter_by(grade_id=selected_grade, school_id=current_user.school_id).all()
        sms_list = [
            {
                "partnerID": "YOUR_PARTNER_ID",
                "apikey": "YOUR_API_KEY",
                "mobile": student.contact_number1,
                "message": message,
                "shortcode": "YOUR_SHORTCODE"
            }
            for student in students
        ]

        from jps_erp.tasks import log_bulk_sms_event  # Delay the import to avoid circular imports
        log_bulk_sms_event.delay(selected_grade, message, success=True)
        # Send bulk SMS asynchronously
        send_bulk_sms_notification.delay(sms_list)

        flash(f'SMS sent to all parents in {selected_grade}', 'success')

        return redirect(url_for('main.send_bulk_sms_route'))
    else:
        log_bulk_sms_event.delay(selected_grade, message, success=False)
        return render_template('main/bulk_sms.html', grades=grades)

@main_bp.route('/dashboard', strict_slashes=False)
@login_required
def dashboard():
    user_name = session.get('user_name')
    school_name = session.get('school_name')

    # Handle missing session data explicitly
    if not user_name or not school_name:
        flash('Session data is missing. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
    log_to_syslog.delay(f"School Name from session: {school_name}", level='info')

    if not current_term:
        flash('No current term set. Please set a current term.', 'info')
        return redirect(url_for('settings.manage_terms'))

    try:
        school_id = current_user.school_id
        term_id = current_term.id
        year = current_year()

        recent_payments_query = get_recent_payments(school_id, limit=10)
        total_active_students = active_students(school_id, term_id)
        total_inactive_students_term = inactive_students_term(school_id, term_id)
        total_inactive_students_year = inactive_students_year(school_id, year)

        total_paid_via_cash_today = paid_via_method_today(school_id, 'Cash')
        total_paid_via_bank_today = paid_via_method_today(school_id, 'Bank')
        total_paid_via_mpesa_today = paid_via_method_today(school_id, 'Mpesa')
        total_banked_today = total_paid_via_bank_today + total_paid_via_mpesa_today


        return render_template('main/dashboard.html', 
                               user_name=user_name, 
                               school_name=school_name, 
                               recent_payments=recent_payments_query, 
                               total_active_students=total_active_students, 
                               total_inactive_students_term=total_inactive_students_term, 
                               total_inactive_students_year=total_inactive_students_year, 
                               total_paid_via_cash_today=total_paid_via_cash_today, 
                               total_banked_today=total_banked_today
                               )
    except Exception as e:
        log_error_event.delay("Error fetching recent payments for dashboard", str(e))
        flash('An error occurred while fetching recent payments.', 'danger')
        return render_template('main/dashboard.html', user_name=user_name, school_name=school_name, recent_payments=[])

    

@main_bp.route('/get_streams/<int:grade_id>', methods=['GET'])
@login_required
def get_streams(grade_id):
    streams = Stream.query.filter_by(grade_id=grade_id).all()
    stream_list = [{'id': stream.id, 'name': stream.name} for stream in streams]
    print(f"Debugging: Streams for grade {grade_id}:", stream_list)
    return jsonify({'streams': stream_list })

