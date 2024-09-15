from sqlalchemy import func
from jps_erp import db
import sqlalchemy as sa
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction, student_additional_fee, Grade
from flask_login import current_user
import pdfplumber
import re
import spacy
from datetime import date
from flask import url_for
from jps_erp.tasks import send_async_email_task

def send_password_reset_email(user, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
      # Delay the import to avoid circular imports
    send_async_email_task.delay(
        subject='Reset Your Password',
        recipient=user.email,
        body=f'''To reset your password, click the following link:
{reset_url}
If you did not make this request, simply ignore this email and no changes will be made.
'''
    )

def register_user(form):
    # Check if the username already exists
    user = User.query.filter_by(username=form.username.data).first()
    if user:
        return None, 'Username already exists.'
    
    # Check if the school already exists
    existing_school = School.query.filter_by(name=form.school_name.data).first()
    
    if existing_school:
        # Check how many users are associated with this school
        user_count = User.query.filter_by(school_id=existing_school.school_id).count()
        if user_count >= 3:
            return None, 'This school already has the maximum number of users.'

        # No need to add the school again, just create a new user for this school
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            school_id=existing_school.school_id
        )
    else:
        # Create a new school and add the first user
        new_school = School(name=form.school_name.data, contacts=form.school_contacts.data)
        db.session.add(new_school)
        db.session.commit()

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            school_id=new_school.school_id
        )

    # Set user password and add the user to the database
    new_user.set_password(form.password.data)
    db.session.add(new_user)
    db.session.commit()

    return new_user, None


class FeeStructureNotFoundError(Exception):
    pass

def calculate_balance(student_id):
    # Fetch the student record
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        raise ValueError("Student not found")
    
    # Get the current term
    current_term = Term.query.filter_by(current=True, school_id=student.school_id).first()
    if not current_term:
        raise ValueError("Current term not found")
    
    # Fetch the fee structure for the student's grade and school
    fee_structure = FeeStructure.query.filter_by(
        grade=student.grade,
        school_id=student.school_id,
        term_id=current_term.id
    ).first()
    if not fee_structure:
        raise FeeStructureNotFoundError("Fee structure not found for the student's grade and school in the current term")
    
    # Calculate the total standard fees for the grade
    total_standard_fees = (
        fee_structure.tuition_fee +
        fee_structure.ass_books +
        fee_structure.diary_fee +
        fee_structure.activity_fee +
        fee_structure.others
    )
    
    # Calculate the total additional fees for the student
    total_additional_fees = (
        db.session.query(sa.func.sum(AdditionalFee.amount))
        .join(student_additional_fee, AdditionalFee.id == student_additional_fee.c.additional_fee_id)
        .filter(student_additional_fee.c.student_id == student_id)
        .scalar() or 0.0
    )
    
    # Get the balance carry forward for the student, including onboarding balance
    previous_term_payment = FeePayment.query.filter(
        FeePayment.student_id == student_id,
        FeePayment.term_id != current_term.id
    ).order_by(FeePayment.term_id.desc()).first()

    # Start with the carry forward balance from onboarding
    carry_forward_balance = student.cf_balance
    
    # Add any outstanding balance from previous term payments
    if previous_term_payment:
        carry_forward_balance += previous_term_payment.balance or 0.0
    
    # Calculate the total amount paid by the student in the current term
    total_paid = db.session.query(sa.func.sum(FeePayment.amount)).filter_by(student_id=student_id, term_id=current_term.id).scalar() or 0.0
    
    # Calculate the balance owed
    balance = (total_standard_fees + total_additional_fees + carry_forward_balance) - total_paid
    
    return balance, carry_forward_balance


nlp = spacy.load('en_core_web_sm')

def extract_transactions_from_pdf(pdf_path):
    transactions = []

    # Regular expression patterns for extracting codes and amounts
    mpesa_code_regex = r"MPS\s254\d{9}\s([A-Z0-9]{10})"
    mpesa_amount_regex = r"\d{2}/\d{2}/\d{4}\s(\d{1,3}(,\d{3})*\.\d{2})"
    bank_code_regex = r"(\d{12})/\d{2}-\d{2}-\d{4}"
    bank_amount_regex = r"\d{2}-\d{2}-\d{4}\s(\d{1,3}(,\d{3})*\.\d{2})"

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            print(f"Debug: Extracted text from page {page_number}:\n{text}\n{'-'*80}")

            if text:
                doc = nlp(text)
                for sentence in doc.sents:
                    line = sentence.text

                    # Extract Mpesa transaction code
                    mpesa_code_match = re.search(mpesa_code_regex, line)
                    if mpesa_code_match:
                        mpesa_code = mpesa_code_match.group(1)
                        print(f"Debug: Extracted Mpesa code - {mpesa_code}")

                        # Find the corresponding amount
                        amount_match = re.search(mpesa_amount_regex, line)
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            transactions.append({'code': mpesa_code, 'amount': amount})
                            print(f"Debug: Extracted Mpesa transaction - Code: {mpesa_code}, Amount: {amount}")

                    # Extract Bank transaction code
                    bank_code_match = re.search(bank_code_regex, line)
                    if bank_code_match:
                        bank_code = bank_code_match.group(1)
                        print(f"Debug: Extracted Bank code - {bank_code}")

                        # Find the corresponding amount
                        amount_match = re.search(bank_amount_regex, line)
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            transactions.append({'code': bank_code, 'amount': amount})
                            print(f"Debug: Extracted Bank transaction - Code: {bank_code}, Amount: {amount}")

    return transactions

def generate_custom_student_id(school_name, school_id):
    school_abbr = ''.join([word[0] for word in school_name.split()]).upper()
    student_count = Student.query.filter_by(school_id=school_id).count() + 1
    student_id = f"{school_abbr}{student_count:03d}"

    # Ensure the custom student ID is unique
    while Student.query.filter_by(student_id=student_id).first():
        student_count += 1
        student_id = f"{school_abbr}{student_count:03d}"

    return student_id


def process_mpesa_transaction(code, amount):
    mpesa_transaction = MpesaTransaction.query.filter_by(code=code).first()
    
    if mpesa_transaction:
        if mpesa_transaction.verified:
            print('Mpesa transaction code has already been used.', 'danger')
            return False
        else:
            # If the code exists but is not verified, update the transaction details
            mpesa_transaction.amount = amount
    else:
        # If the code does not exist, create a new transaction entry
        mpesa_transaction = MpesaTransaction(code=code, amount=amount, verified=False)
    
    db.session.add(mpesa_transaction)
    db.session.commit()

    return True

def get_current_term(school_id):
    return Term.query.filter_by(school_id=school_id, current=True).first()

def get_recent_payments(school_id, limit=None):
    query = db.session.query(
            Student.full_name,
            Grade.name,
            FeePayment.amount,
            FeePayment.method,
            FeePayment.code,
            MpesaTransaction.verified
        )\
        .join(FeePayment.student)\
        .join(Grade, Student.grade_id == Grade.id)\
        .outerjoin(MpesaTransaction, FeePayment.code == MpesaTransaction.code)\
        .filter(FeePayment.school_id == school_id)\
        .order_by(FeePayment.pay_date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()

def active_students(school_id, term_id):
    return db.session.query(func.count(Student.student_id))\
        .filter(Student.school_id == school_id, Student.current_term_id == term_id, Student.active == True)\
        .scalar()

def inactive_students_term(school_id, term_id):
    return db.session.query(func.count(Student.student_id))\
        .filter(Student.school_id == school_id, Student.current_term_id == term_id, Student.active == False)\
        .scalar()

def inactive_students_year(school_id, year):
    return db.session.query(func.count(Student.student_id))\
        .join(Term, Student.current_term_id == Term.id)\
        .filter(Student.school_id == school_id, Term.year == year, Student.active == False)\
        .scalar()

def paid_via_method_term(school_id, term_id, method):
    return db.session.query(func.sum(FeePayment.amount))\
        .filter(FeePayment.school_id == school_id, FeePayment.term_id == term_id, FeePayment.method == method)\
        .scalar() or 0.0

def paid_via_method_year(school_id, year, method):
    return db.session.query(func.sum(FeePayment.amount))\
        .join(Term, FeePayment.term_id == Term.id)\
        .filter(FeePayment.school_id == school_id, Term.year == year, FeePayment.method == method)\
        .scalar() or 0.0


def current_year():
    return date.today().year

def current_date():
    return date.today()

def paid_via_method_today(school_id, method):
    today = current_date()
    return db.session.query(func.sum(FeePayment.amount))\
        .filter(FeePayment.school_id == school_id, FeePayment.method == method, func.date(FeePayment.pay_date) == today)\
        .scalar() or 0.0

def get_grade_info(grade, current_term, school_id):
    fee_structure = FeeStructure.query.filter_by(
        grade_id=grade.id,
        term_id=current_term.id,
        school_id=school_id
    ).first()

    total_students = Student.query.filter_by(grade_id=grade.id, school_id=school_id).count()

    expected_fees = (
        fee_structure.tuition_fee +
        fee_structure.ass_books +
        fee_structure.diary_fee +
        fee_structure.activity_fee +
        fee_structure.others
    ) * total_students if fee_structure else 0

    total_fees_paid = db.session.query(func.sum(FeePayment.amount)).join(
        Student, FeePayment.student_id == Student.student_id
    ).filter(
        Student.grade_id == grade.id,
        Student.school_id == school_id,
        FeePayment.term_id == current_term.id
    ).scalar() or 0.0

    return {
        'grade_name': grade.name,
        'expected_fees': expected_fees,
        'total_fees_paid': total_fees_paid,
        'total_balance': expected_fees - total_fees_paid,
        'total_students': total_students
    }

def get_additional_fees_info(grade, current_term, school_id):
    additional_fees = db.session.query(
        AdditionalFee.fee_name,
        func.count(Student.student_id).label('student_count'),
        func.sum(AdditionalFee.amount).label('total_amount'),
        func.group_concat(Student.full_name).label('student_names')
    ).join(
        AdditionalFee.students
    ).filter(
        Student.grade_id == grade.id,
        Student.school_id == school_id,
        Student.current_term_id == current_term.id
    ).group_by(AdditionalFee.id).all()

    return [
        {
            'fee_name': fee.fee_name,
            'student_count': fee.student_count,
            'total_amount': fee.total_amount,
            'students': fee.student_names.split(',')
        }
        for fee in additional_fees
    ]

def get_payment_method_comparison(current_term, previous_term, school_id):
    def get_payment_methods(term):
        return db.session.query(
            FeePayment.method,
            func.sum(FeePayment.amount).label('total_amount')
        ).filter(
            FeePayment.term_id == term.id,
            FeePayment.school_id == school_id
        ).group_by(FeePayment.method).all()

    # Get current term payment methods
    current_methods = get_payment_methods(current_term)
    current_total = sum(method.total_amount for method in current_methods)

    # Initialize previous methods to empty if no previous term exists
    if previous_term:
        previous_methods = get_payment_methods(previous_term)
        previous_total = sum(method.total_amount for method in previous_methods)
    else:
        previous_methods = []
        previous_total = 0

    return {
        'current': {method.method: (method.total_amount / current_total) * 100 for method in current_methods},
        'previous': {method.method: (method.total_amount / previous_total) * 100 for method in previous_methods} if previous_total > 0 else {}
    }

def get_term_comparison(current_term, previous_term, school_id):
    def get_term_data(term):
        if term is None:
            return {}

        grades = Grade.query.filter_by(school_id=school_id).all()
        term_data = {}
        for grade in grades:
            total_fees = db.session.query(func.sum(FeePayment.amount)).join(
                Student, FeePayment.student_id == Student.student_id
            ).filter(
                Student.grade_id == grade.id,
                Student.school_id == school_id,
                FeePayment.term_id == term.id
            ).scalar() or 0.0

            additional_fees = db.session.query(
                func.sum(AdditionalFee.amount).label('total_amount'),
                func.count(Student.student_id).label('student_count')
            ).join(
                AdditionalFee.students
            ).filter(
                Student.grade_id == grade.id,
                Student.school_id == school_id,
                Student.current_term_id == term.id
            ).first()

            term_data[grade.name] = {
                'total_fees': total_fees,
                'additional_fees': additional_fees.total_amount or 0,
                'additional_fees_count': additional_fees.student_count or 0
            }
        return term_data

    return {
        'current': get_term_data(current_term),
        'previous': get_term_data(previous_term)
    }

def get_additional_fees_comparison(current_term, previous_term, school_id):
    def get_additional_fees_data(term):
        # If term is None, return an empty dictionary
        if term is None:
            return {}
            
        grades = Grade.query.filter_by(school_id=school_id).all()
        term_data = {}
        for grade in grades:
            additional_fees = db.session.query(
                func.sum(AdditionalFee.amount).label('total_amount'),
                func.count(Student.student_id).label('student_count')
            ).join(
                AdditionalFee.students
            ).filter(
                Student.grade_id == grade.id,
                Student.school_id == school_id,
                Student.current_term_id == term.id
            ).first()

            term_data[grade.name] = {
                'total_amount': additional_fees.total_amount or 0,
                'student_count': additional_fees.student_count or 0
            }
        return term_data

    return {
        'current': get_additional_fees_data(current_term),
        'previous': get_additional_fees_data(previous_term)
    }
