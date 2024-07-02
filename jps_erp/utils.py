from sqlalchemy import func
from jps_erp import app, db
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction, student_additional_fee
from flask_login import current_user
import pdfplumber
import re

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

        raise ValueError("Fee structure not found for the student's grade and school in the current term")
    
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

def extract_transactions_from_pdf(pdf_path):
    transactions = []

    # Regular expression patterns for extracting codes and amounts
    mpesa_pattern = re.compile(r'\b\w{10}\b')
    bank_pattern = re.compile(r'\b\d{12}\b')
    amount_pattern = re.compile(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b')

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            print(f"Debug: Extracted text from page {page_number}:\n{text}\n{'-'*80}")

            if text:
                lines = text.split('\n')
                for line in lines:
                    # Clean up the line to remove OCR artifacts
                    cleaned_line = re.sub(r'[^A-Za-z0-9\s.,#@]', '', line)

                    # Check for transaction code (Mpesa or bank)
                    mpesa_match = mpesa_pattern.search(cleaned_line)
                    bank_match = bank_pattern.search(cleaned_line)
                    code = mpesa_match.group(0) if mpesa_match else (bank_match.group(0) if bank_match else None)

                    # Check for amount
                    amount_match = amount_pattern.search(cleaned_line)
                    amount = float(amount_match.group(0).replace(',', '')) if amount_match else None

                    if code and amount is not None:
                        transactions.append({'code': code, 'amount': amount})
                        print(f"Debug: Extracted transaction - Code: {code}, Amount: {amount}")

    return transactions