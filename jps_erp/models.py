from jps_erp import db, login_manager
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String(20), nullable=False)
    role = sa.Column(sa.String(20), nullable=False)
    password_hash = sa.Column(sa.String(256), nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    school = so.relationship('School', back_populates='users')
    audits = so.relationship('Audit', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"

class School(db.Model):
    school_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(100), nullable=False)
    contacts = sa.Column(sa.String(100), nullable=False)
    
    fee_structures = so.relationship('FeeStructure', back_populates='school', lazy=True)
    users = so.relationship('User', back_populates='school', lazy=True)
    students = so.relationship('Student', back_populates='school', lazy=True)
    fee_payments = so.relationship('FeePayment', back_populates='school', lazy=True)
    audits = so.relationship('Audit', back_populates='school', lazy=True)
    additional_fees = so.relationship('AdditionalFee', back_populates='school', lazy=True)

class FeeStructure(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    grade = sa.Column(sa.String(10), nullable=False)
    tuition_fee = sa.Column(sa.Float, nullable=False)
    ass_books = sa.Column(sa.Float, nullable=False)
    diary_fee = sa.Column(sa.Float, nullable=False)
    activity_fee = sa.Column(sa.Float, nullable=False)
    others = sa.Column(sa.Float, nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    term_id = sa.Column(sa.Integer, sa.ForeignKey('term.id'), nullable=False)
    
    school = so.relationship('School', back_populates='fee_structures')
    term = so.relationship('Term', back_populates='fee_structures')

    __table_args__ = (
        sa.UniqueConstraint('grade', 'school_id', 'term_id', name='unique_grade_school_term'),
    )

student_additional_fee = sa.Table('student_additional_fee', db.Model.metadata,
    sa.Column('student_id', sa.String, sa.ForeignKey('student.student_id'), primary_key=True),
    sa.Column('additional_fee_id', sa.Integer, sa.ForeignKey('additional_fee.id'), primary_key=True)
)

class AdditionalFee(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    fee_name = sa.Column(sa.String(100), nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    #student_id = sa.Column(sa.Integer, sa.ForeignKey('student.student_id'), nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    school = so.relationship('School', back_populates='additional_fees')
    students = so.relationship('Student', secondary=student_additional_fee, back_populates='additional_fees')
    
"""
class StudentAdditionalFee(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    student_id = sa.Column(sa.Integer, sa.ForeignKey('student.student_id'), nullable=False)
    additional_fee_id = sa.Column(sa.Integer, sa.ForeignKey('additional_fee.id'), nullable=False)
    
    student = so.relationship('Student', back_populates='additional_fee')
    additional_fee = so.relationship('AdditionalFee', back_populates='students')
"""
class Student(db.Model):
    student_id = sa.Column(sa.String(10), primary_key=True, unique=True, nullable=False)
    full_name = sa.Column(sa.String(100), nullable=False)
    dob = sa.Column(sa.String(10), nullable=False)
    gender = sa.Column(sa.String(10), nullable=False)
    guardian_name = sa.Column(sa.String(100), nullable=False)
    contact_number1 = sa.Column(sa.String(20), nullable=False)
    contact_number2 = sa.Column(sa.String(20), nullable=False)
    grade = sa.Column(sa.String(10), nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    active = sa.Column(sa.Boolean, default=True, nullable=False)  # Indicates if the student is currently enrolled
    left_date = sa.Column(sa.Date, nullable=True)  # Date when the student left, if applicable
    current_term_id = sa.Column(sa.Integer, sa.ForeignKey('term.id'), nullable=True)  # Current term of the student
    year = sa.Column(sa.Integer, nullable=False)
    
    school = so.relationship('School', back_populates='students')
    fee_payments = so.relationship('FeePayment', back_populates='student', lazy=True)
    additional_fees = so.relationship('AdditionalFee', secondary=student_additional_fee, back_populates='students')
    current_term = so.relationship('Term', back_populates='students', foreign_keys=[current_term_id])

    def __repr__(self):
        return f"Student('{self.full_name}', '{self.student_id}', '{self.grade}', '{self.school_id}')"

class FeePayment(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True, unique=True)
    method = sa.Column(sa.String(50), nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    pay_date = sa.Column(sa.Date, nullable=False)
    code = sa.Column(sa.String(20), nullable=True, unique=True)
    balance = sa.Column(sa.Float, nullable=False)
    cf_balance = sa.Column(sa.Float, default=0.0)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    student_id = sa.Column(sa.String, sa.ForeignKey('student.student_id'), nullable=False)
    term_id = sa.Column(sa.Integer, sa.ForeignKey('term.id'), nullable=False)

    term = so.relationship('Term', back_populates='fee_payments')
    school = so.relationship('School', back_populates='fee_payments')
    student = so.relationship('Student', back_populates='fee_payments')
    mpesa_transaction = so.relationship('MpesaTransaction', primaryjoin="FeePayment.code == MpesaTransaction.code", foreign_keys=[code], uselist=False)


    def __repr__(self):
        return f"FeePayment('{self.method}', Amount: '{self.amount}', Balance: '{self.balance}', Carry Forward: '{self.cf_balance}')"

class MpesaTransaction(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    code = sa.Column(sa.String(20), unique=True, nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    verified = sa.Column(sa.Boolean, default=False)
    

    def __repr__(self):
        return f"MpesaTransaction('{self.code}', Verified: {self.verified}, Amount: {self.amount})"

class BankStatement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    
class Term(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(50), nullable=False)  # e.g., "Term 1 2023"
    start_date = sa.Column(sa.Date, nullable=False)
    end_date = sa.Column(sa.Date, nullable=False)
    year = sa.Column(sa.Integer, nullable=False)
    current = sa.Column(sa.Boolean, default=False, nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    students = so.relationship('Student', back_populates='current_term')
    fee_payments = so.relationship('FeePayment', back_populates='term')
    fee_structures = so.relationship('FeeStructure', back_populates='term')

    #__table_args__ = (sa.UniqueConstraint('name', 'year', name='unique_term_name_year'),
    #)
    
    def __repr__(self):
        return f"Term('{self.name}',  '{self.year}', '{self.start_date}', '{self.end_date}')"


class Audit(db.Model):
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True, unique=True)
    action = sa.Column(sa.String(50), nullable=False)
    details = sa.Column(sa.String(100), nullable=False)
    timestamp = sa.Column(sa.DateTime, default=sa.func.current_timestamp(), nullable=False)
    
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    
    school = so.relationship('School', back_populates='audits')
    user = so.relationship('User', back_populates='audits')

    def __repr__(self):
        return f"Audit('{self.action}', '{self.timestamp}')"