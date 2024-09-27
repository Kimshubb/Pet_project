from . import payments_bp
from flask import render_template, url_for, flash, redirect, request, session, current_app
from jps_erp import db
from jps_erp.models import FeePayment, Student, Term, MpesaTransaction, Grade, Stream, FeeStructure, AdditionalFee, student_additional_fee, BankStatement
from jps_erp.forms import Fee_paymentForm, AssociateFeeForm
from jps_erp.utils import calculate_balance, extract_transactions_from_pdf, get_recent_payments, FeeStructureNotFoundError, get_grade_info, get_additional_fees_info, get_additional_fees_comparison, get_payment_method_comparison, get_term_comparison, get_additional_fees_info
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import qrcode
import io
import base64

@payments_bp.context_processor
def utility_processor():
    return dict(str=str)

@payments_bp.route('/new_payment', methods=['POST', 'GET'])
@login_required
def new_payment():
    form = Fee_paymentForm()

    if form.validate_on_submit():
        try:
            current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
            if not current_term:
                raise ValueError('No current term is set. Please set a current term before making payments.')

            student = Student.query.filter_by(student_id=form.student_id.data, school_id=current_user.school_id).first()
            if not student:
                raise ValueError('Student not found')

            balance, carry_forward_balance = calculate_balance(student.student_id)
            
            # Check if the payment method is Mpesa
            if form.method.data == 'Mpesa':
                # Check if the transaction code already exists in the database
                existing_transaction = MpesaTransaction.query.filter_by(code=form.code.data).first()
                if existing_transaction:
                    raise ValueError('This Mpesa transaction code has already been used. Please enter a new code.')
                
                # Create a new MpesaTransaction
                new_mpesa_transaction = MpesaTransaction(
                    code=form.code.data,
                    amount=form.amount.data,
                    verified=False  # Assuming the transaction is verified upon entry
                )
                db.session.add(new_mpesa_transaction)
            
            new_payment = FeePayment(
                method=form.method.data,
                amount=form.amount.data,
                code=form.code.data if form.method.data in ['Mpesa', 'Bank'] else None,
                balance=balance - form.amount.data,
                school_id=current_user.school_id,
                student_id=student.student_id,
                pay_date=datetime.today().date(),
                term_id=current_term.id
            )

            db.session.add(new_payment)
            
            # Update student's carry forward balance
            student.cf_balance = max(0, balance - form.amount.data)
            
            db.session.commit()
            
            flash('Payment added successfully', 'success')
            return redirect(url_for('payments.print_receipt', student_id=student.student_id, payment_id=new_payment.id))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            current_app.logger.error(f"Error in new_payment: {str(e)}", exc_info=True)

    payments = FeePayment.query.filter_by(school_id=current_user.school_id).all()
    return render_template('payments/new_payment.html', form=form, payments=payments)
"""
@payments_bp.route('/new_payment', methods=['POST', 'GET'])
@login_required
def new_payment():
    form = Fee_paymentForm()

    if form.validate_on_submit():
        current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
        if not current_term:
            flash('No current term is set. Please set a current term before making payments.', 'danger')
            return redirect(url_for('payments.new_payment'))
        print(f"Current term ID: {current_term.id}")


        pay_date = datetime.today().date()
        student_id = form.student_id.data
        method = form.method.data
        amount = float(form.amount.data)
        code = form.code.data if method in ['Mpesa', 'Bank'] else None  # Get the code from the form
        school_id = current_user.school_id
        term_id = current_term.id

        print(f"Payment date: {pay_date}")
        print(f"Student ID: {student_id}")
        print(f"Method: {method}")
        print(f"Amount: {amount}")
        print(f"Code: {code}")
        print(f"School ID: {school_id}")
        print(f"Term ID: {term_id}")


        # Check if student exists in the current user's school
        student = Student.query.filter_by(student_id=student_id, school_id=current_user.school_id).first()
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('payments.new_payment'))

        # Calculate current balance and carry forward balance
        balance, cf_balance = calculate_balance(student_id)

        print(f"Current balance: {balance}")
        print(f"Carry forward balance: {cf_balance}")

        if method == 'Mpesa':
            # Check if the Mpesa transaction code has already been used
            mpesa_transaction = MpesaTransaction.query.filter_by(code=code).first()
            if mpesa_transaction and mpesa_transaction.used:
                flash('Mpesa transaction code has already been used.', 'danger')
                return redirect(url_for('payments.new_payment'))

            # Verify the Mpesa transaction using the code from the form
            #if not check_transaction_status(code):
             #   flash('Mpesa transaction verification failed. Please try again.', 'danger')
              #  return redirect(url_for('new_payment'))

            # Mark the transaction code as used
            if mpesa_transaction:
                mpesa_transaction.used = True
            else:
                mpesa_transaction = MpesaTransaction(code=code, verified=True, used=True)
            db.session.add(mpesa_transaction)
            db.session.commit()

        new_payment = FeePayment(
            method=method,
            amount=amount,
            code=code,
            balance=balance - amount,  # Update balance after the new payment
            cf_balance=cf_balance,
            school_id=school_id,
            student_id=student.student_id,
            pay_date=pay_date,
            term_id=term_id
        )

        try:
            db.session.add(new_payment)
            db.session.commit()
            flash('Payment added successfully', 'success')
            print(f"New payment added with ID: {new_payment.id}")
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding payment: {str(e)}', 'danger')
            print(f"Error adding payment: {str(e)}")

        return redirect(url_for('payments.print_receipt', student_id=student.student_id, payment_id=new_payment.id))

    print("Form did not validate", form.errors)
    payments = FeePayment.query.filter_by(school_id=current_user.school_id).all()
    return render_template('payments/new_payment.html', form=form, payments=payments)
"""
@payments_bp.route('/student_payments', methods=['GET'])
@login_required
def student_payments():
    grade_filter = request.args.get('grade', 'all')
    stream_filter = request.args.get('stream', 'all')
    #paginate
    page = request.args.get('page', 1, type=int)
    per_page = 15

    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()

    query = Student.query.filter_by(school_id=current_user.school_id, active=True)
    
    if grade_filter != 'all':
        query = query.filter_by(grade_id=grade_filter)
    
    if stream_filter != 'all':
        query = query.filter_by(stream_id=stream_filter)
    
    students_paginated = query.paginate(page=page, per_page=per_page)

    student_payment_details = []

    for student in students_paginated.items:
        total_paid = db.session.query(func.sum(FeePayment.amount)).filter_by(student_id=student.student_id, term_id=current_term.id).scalar() or 0.0
        try:
            balance, cf_balance = calculate_balance(student.student_id)
        except FeeStructureNotFoundError as e:
            flash(str(e), 'warning')
            return redirect(url_for('settings.manage_fee_structure'))

        student_payment_details.append({
            'student': student,
            'cf_balance': cf_balance,
            'total_paid': total_paid,
            'balance': balance
        })

    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    streams = Stream.query.filter(Stream.grade_id.in_([grade.id for grade in grades])).all()

    return render_template('payments/student_payments.html', 
                           student_payment_details=student_payment_details, 
                           current_term=current_term, 
                           grades=grades, 
                           streams=streams, 
                           selected_grade=grade_filter,
                           students_paginated=students_paginated, 
                           selected_stream=stream_filter)

"""
@payments_bp.route('/student/<string:student_id>/receipt/<int:payment_id>', methods=['GET'])
@login_required
def print_receipt(student_id, payment_id):
    student = Student.query.get_or_404(student_id)
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
    school = current_user.school

    if payment_id == 0:  # Generate a fee statement instead of a single payment receipt
        payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.pay_date).all()
        total_paid = sum(payment.amount for payment in payments)
        balance, cf_balance = calculate_balance(student_id)

        return render_template('payments/fee_statement.html', student=student, payments=payments, balance=balance, cf_balance=cf_balance, total_paid=total_paid, current_term=current_term, school=school)
    else:
        payment = FeePayment.query.get_or_404(payment_id)
        balance, cf_balance = calculate_balance(student_id)

        return render_template('payments/receipt.html', student=student, payment=payment, balance=balance, cf_balance=cf_balance, current_term=current_term, school=school)
"""
@payments_bp.route('/student/<string:student_id>/receipt/<int:payment_id>', methods=['GET'])
@login_required
def print_receipt(student_id, payment_id):
    student = Student.query.get_or_404(student_id)
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
    school = current_user.school

    if payment_id == 0:  # Generate a fee statement instead of a single payment receipt
        payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.pay_date).all()
        total_paid = sum(payment.amount for payment in payments)
        balance, cf_balance = calculate_balance(student_id)

        return render_template('payments/fee_statement.html', student=student, payments=payments, balance=balance, cf_balance=cf_balance, total_paid=total_paid, current_term=current_term, school=school)
    else:
        payment = FeePayment.query.get_or_404(payment_id)
        balance, cf_balance = calculate_balance(student_id)

        # Generate QR code
        fee_statement_url = url_for('payments.print_receipt', student_id=student_id, payment_id=0, _external=True)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(fee_statement_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert QR code image to base64 string
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        return render_template('payments/receipt.html', student=student, payment=payment, balance=balance, cf_balance=cf_balance, current_term=current_term, school=school, qr_code=qr_code)

@payments_bp.route('/recent_payments', strict_slashes=False)
@login_required
def recent_payments():
    try:
        # Fetch all recent payments
        recent_payments_query = get_recent_payments(current_user.school_id, limit=None)  # No limit to get all payments

        # Logging the fetched payments for debugging
        print(f"All Recent Payments: {recent_payments_query}")

        return render_template('payments/recent_payments.html', recent_payments=recent_payments_query)
    except Exception as e:
        print(f"Error fetching all recent payments: {e}")
        flash('An error occurred while fetching recent payments.', 'danger')
        return render_template('payments/recent_payments.html', recent_payments=[])

@payments_bp.route('/fee_reports', methods=['GET'])
@login_required
def fee_reports():
    school_id = current_user.school_id
    current_term = Term.query.filter_by(current=True, school_id=school_id).first()
    previous_term = Term.query.filter(Term.school_id == school_id, Term.end_date < current_term.start_date).order_by(Term.end_date.desc()).first()

    grades = Grade.query.filter_by(school_id=school_id).all()

    grade_details = []
    for grade in grades:
        grade_info = get_grade_info(grade, current_term, school_id)
        additional_fees_info = get_additional_fees_info(grade, current_term, school_id)
        grade_details.append({**grade_info, 'additional_fees': additional_fees_info})

    payment_method_comparison = get_payment_method_comparison(current_term, previous_term, school_id)
    term_comparison = get_term_comparison(current_term, previous_term, school_id)
    additional_fees_comparison = get_additional_fees_comparison(current_term, previous_term, school_id)

    return render_template('payments/fee_reports.html',
                           grade_details=grade_details,
                           payment_method_comparison=payment_method_comparison,
                           term_comparison=term_comparison,
                           additional_fees_comparison=additional_fees_comparison)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

@payments_bp.route('/upload_statement', methods=['GET', 'POST'])
@login_required
def upload_statement():
    print("Debug: Inside upload_statement route")
    if request.method == 'POST':
        print("Debug: POST request detected")
        if 'file' not in request.files:
            print("Debug: No file part in request")
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print("Debug: No selected file")
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print(f"Debug: File {file.filename} is allowed")
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            
            # Ensure the upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file.save(filepath)
            print(f"Debug: File saved to {filepath}")

            bank_statement = BankStatement(filename=filename)
            db.session.add(bank_statement)
            db.session.commit()
            print(f"Debug: Bank statement record added to database with filename {filename}")

            # Extract transaction codes from the PDF
            extracted_transactions = extract_transactions_from_pdf(filepath)
            print(f"Debug: Extracted transactions: {extracted_transactions}")
            
            # Store extracted transactions in session for verification
            session['extracted_transactions'] = extracted_transactions
            
            flash('File uploaded and transactions extracted successfully.', 'success')
            return redirect(url_for('payments.verify_transactions'))

    print("Debug: GET request detected")
    return render_template('payments/verify_transactions.html')

@payments_bp.route('/verify_transactions', methods=['GET', 'POST'])
@login_required
def verify_transactions():
    print("Debug: Inside verify_transactions route")

    # Retrieve extracted transactions from the session
    extracted_transactions = session.get('extracted_transactions', [])
    print(f"Debug: Extracted transactions from session: {extracted_transactions}")

    # Convert extracted transactions to a dictionary for fast lookup
    extracted_transaction_codes = {t['code']: t for t in extracted_transactions}

    page = request.args.get('page', 1, type=int)
    per_page = 15 # Number of records per page

    verified_count = 0
    unverified_transactions = []
    pagination = None

    if request.method == 'POST':
        print("Debug: POST request detected for verification")

        # Query the FeePayments table for all transactions that have a code (linked to MpesaTransactions)
        # Use pagination to fetch a limited number of records at a time
        pagination = FeePayment.query.filter(FeePayment.code.isnot(None)).paginate(page=page, per_page=per_page)
        receipted_payments = pagination.items

        for payment in receipted_payments:
            code = payment.code
            print(f"Debug: Checking payment - Code: {code}, Amount: {payment.amount}")

            # Check if this payment's code is in the extracted transactions
            if code in extracted_transaction_codes:
                extracted_transaction = extracted_transaction_codes[code]
                if payment.amount == extracted_transaction['amount']:
                    verified_count += 1
                    print(f"Debug: Payment verified - Code: {code}, Amount: {payment.amount}")
                else:
                    # Amount mismatch, consider unverified
                    student = payment.student
                    unverified_transactions.append({
                        'code': code,
                        'amount': payment.amount,
                        'student': student.full_name if student else 'Unknown Student',
                        'reason': 'Amount mismatch'
                    })
                    print(f"Debug: Amount mismatch for payment - Code: {code}, Database Amount: {payment.amount}, Extracted Amount: {extracted_transaction['amount']}")
            else:
                # Code not found in extracted transactions, consider unverified
                student = payment.student
                unverified_transactions.append({
                    'code': code,
                    'amount': payment.amount,
                    'student': student.full_name if student else 'Unknown Student',
                    'reason': 'Code not found in statement'
                })
                print(f"Debug: Code not found in statement for payment - Code: {code}, Amount: {payment.amount}")

        print(f"Debug: Verification complete - Verified Count: {verified_count}, Unverified Transactions: {len(unverified_transactions)}")

    return render_template('payments/verify_transactions.html', 
                           verified_count=verified_count, 
                           unverified_transactions=pagination,  # Pass the pagination object
                           paginated_unverified_transactions=unverified_transactions)


@payments_bp.route('/student/<string:student_id>/add_fee', methods=['GET', 'POST'])
@login_required
def add_additional_fee(student_id):
    student = Student.query.get_or_404(student_id)
    form = AssociateFeeForm()
    form.additional_fee_id.choices = [(fee.id, fee.fee_name) for fee in AdditionalFee.query.filter_by(school_id=current_user.school_id).all()]

    if form.validate_on_submit():
        additional_fee_id = form.additional_fee_id.data
        # Check if the association already exists
        existing_association = db.session.query(Student).join(student_additional_fee).filter(
            student_additional_fee.c.student_id == student_id,
            student_additional_fee.c.additional_fee_id == additional_fee_id
        ).first()

        if existing_association:
            flash('This additional fee is already associated with the student.', 'warning')
        else:
            fee = AdditionalFee.query.get(additional_fee_id)
            student.additional_fees.append(fee)
            db.session.commit()
            flash('Additional fee added successfully', 'success')

        return redirect(url_for('payments.add_additional_fee', student_id=student_id))

    # Fetch the additional fees already associated with the student
    associated_fees = student.additional_fees

    return render_template('payments/add_additionalfee.html', student=student, form=form, associated_fees=associated_fees)