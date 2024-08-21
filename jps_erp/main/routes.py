from . import main_bp
from flask import render_template, redirect, url_for, flash, session, jsonify
from jps_erp.models import Term, Stream
from jps_erp.utils import current_year, get_recent_payments, active_students, inactive_students_term, inactive_students_year, paid_via_method_today
from flask_login import login_required, current_user


@main_bp.route('/dashboard', strict_slashes=False)
@login_required
def dashboard():
    user_name = session.get('user_name', 'User')  # Getting user name from session
    school_name = session.get('school_name', 'Your School')  # Getting school name from session
    current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
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

        #total_paid_via_cash_term = paid_via_method_term(school_id, term_id, 'Cash')
        #total_paid_via_cash_year = paid_via_method_year(school_id, year, 'Cash')

        #total_paid_via_bank_term = paid_via_method_term(school_id, term_id, 'Bank')
        #total_paid_via_bank_year = paid_via_method_year(school_id, year, 'Bank')

        #total_paid_via_mpesa_term = paid_via_method_term(school_id, term_id, 'Mpesa')
        #total_paid_via_mpesa_year = paid_via_method_year(school_id, year, 'Mpesa')

        total_paid_via_cash_today = paid_via_method_today(school_id, 'Cash')
        total_paid_via_bank_today = paid_via_method_today(school_id, 'Bank')
        total_paid_via_mpesa_today = paid_via_method_today(school_id, 'Mpesa')
        total_banked_today = total_paid_via_bank_today + total_paid_via_mpesa_today

        # Logging the fetched payments for debugging
        print(f"Dashboard Recent Payments: {recent_payments_query}")

        return render_template('main/dashboard.html', user_name=user_name, school_name=school_name, recent_payments=recent_payments_query, 
                               total_active_students=total_active_students, total_inactive_students_term=total_inactive_students_term, 
                               total_inactive_students_year=total_inactive_students_year, total_paid_via_cash_today=total_paid_via_cash_today, 
                               total_banked_today=total_banked_today
                               )
    except Exception as e:
        print(f"Error fetching recent payments for dashboard: {e}")
        flash('An error occurred while fetching recent payments.', 'danger')
        return render_template('main/dashboard.html', user_name=user_name, school_name=school_name, recent_payments=[])
    

@main_bp.route('/get_streams/<int:grade_id>', methods=['GET'])
@login_required
def get_streams(grade_id):
    streams = Stream.query.filter_by(grade_id=grade_id).all()
    stream_list = [{'id': stream.id, 'name': stream.name} for stream in streams]
    print(f"Debugging: Streams for grade {grade_id}:", stream_list)
    return jsonify({'streams': stream_list })

