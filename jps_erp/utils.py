from sqlalchemy import func
from jps_erp import app, db
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction, student_additional_fee
from flask_login import current_user
import pdfplumber
import re
import spacy
from datetime import date

class FeeStructureNotFoundError(Exception):
    pass

def calculate_balance(student_id):
    # Fetch the student record
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        raise ValueError("Student not found")
    
    # Get the current term
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
    if not current_term:
        raise ValueError("Current term not found")
    
    # Fetch the fee structure for the student's grade and school
    fee_structure = FeeStructure.query.filter_by(
        grade=student.grade,
        school_id=student.school_id,
        term_id=current_term.id
    ).first()
    print("Debug fee structure query", fee_structure)
    if not fee_structure:
        print(f"Grade: {student.grade}, School ID: {student.school_id}, Term name: {current_term.name}, Term year: {current_term.year}")

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
        db.session.query(func.sum(AdditionalFee.amount))
        .join(student_additional_fee, AdditionalFee.id == student_additional_fee.c.additional_fee_id)
        .filter(student_additional_fee.c.student_id == student_id)
        .scalar() or 0.0
    )
    
    # Get the balance carry forward for the student
    previous_term_payment = FeePayment.query.filter(
        FeePayment.student_id == student_id,
        FeePayment.term_id != current_term.id
    ).order_by(FeePayment.term_id.desc()).first()
    carry_forward_balance = previous_term_payment.balance if previous_term_payment else 0.0
    
    # Calculate the total amount paid by the student
    total_paid = db.session.query(func.sum(FeePayment.amount)).filter_by(student_id=student_id, term_id=current_term.id).scalar() or 0.0
    
    # Calculate the balance
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

def get_recent_payments(school_id, limit=None):
    query = db.session.query(
            Student.full_name,
            Student.grade,
            FeePayment.amount,
            FeePayment.method,
            FeePayment.code,
            MpesaTransaction.verified
        )\
        .join(Student, FeePayment.student_id == Student.student_id)\
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

def get_current_term(school_id):
    return db.session.query(Term.id).filter(Term.current == True, Term.school_id == school_id).scalar()

def current_year():
    return date.today().year

def current_date():
    return date.today()

def paid_via_method_today(school_id, method):
    today = current_date()
    return db.session.query(func.sum(FeePayment.amount))\
        .filter(FeePayment.school_id == school_id, FeePayment.method == method, func.date(FeePayment.pay_date) == today)\
        .scalar() or 0.0
