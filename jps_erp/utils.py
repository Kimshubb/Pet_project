from sqlalchemy import func
from jps_erp import app, db
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction, student_additional_fee
from flask_login import current_user

def calculate_balance(student_id):
    # Fetch the student record
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        raise ValueError("Student not found")
    
    # Get the current term
    current_term = Term.query.filter_by(current=True).first()
    if not current_term:
        raise ValueError("Current term not found")
    
    # Fetch the fee structure for the student's grade and school
    fee_structure = FeeStructure.query.filter_by(
        grade=student.grade,
        school_id=student.school_id,
        term_id=current_term.id
    ).first()
    if not fee_structure:
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

