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
    id = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    username = so.mapped_column(sa.String(20), nullable=False)
    role = so.mapped_column(sa.String(20), nullable=False)
    password_hash = so.mapped_column(sa.String(256), nullable=False)
    school_id = so.mapped_column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    school = so.relationship('School', backref='user_school')
    audits = so.relationship('Audit', backref='audit_user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"


class School(db.Model):
    school_id = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name = so.mapped_column(sa.String(100), nullable=False)
    contacts = so.mapped_column(sa.String(100), nullable=False)
    
    fee_structures = so.relationship('FeeStructure', backref='school_fee_structure', lazy=True)
    user_accounts = so.relationship('User', backref='school_user_account', lazy=True)
    audits = so.relationship('Audit', backref='school_audit', lazy=True)
    fee_payments = so.relationship('FeePayment', backref='school_fee_payment', lazy=True)
    students = so.relationship('Student', backref='school_student', lazy=True)

class FeeStructure(db.Model):
    grade = sa.Column(sa.String(10), primary_key=True)
    tuition_fee = sa.Column(sa.Float, nullable=False)
    ass_books = sa.Column(sa.Float, nullable=False)
    diary_fee = sa.Column(sa.Float, nullable=False)
    activity_fee = sa.Column(sa.Float, nullable=False)
    others = sa.Column(sa.Float, nullable=False)
    school_id = sa.Column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    #additional_fees = so.relationship('AdditionalFee', backref='fee_structure_additional_fee', lazy=True)
    students = so.relationship('Student', backref='fee_structure', lazy=True)

#class AdditionalFee(db.Model):
   # id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    #fee_name = sa.Column(sa.String(100), nullable=False)
    #payable_amount = sa.Column(sa.Float, nullable=False)
    #fee_structure_grade = sa.Column(sa.String(10), sa.ForeignKey('fee_structure.grade'), nullable=False)

class Student(db.Model):
    student_id = so.mapped_column(sa.Integer, primary_key=True, unique=True, autoincrement=True)
    full_name = so.mapped_column(sa.String(100), nullable=False)
    dob = so.mapped_column(sa.String(10), nullable=False)
    gender = so.mapped_column(sa.String(10), nullable=False)
    guardian_name = so.mapped_column(sa.String(100), nullable=False)
    contact_number1 = so.mapped_column(sa.String(20), nullable=False)
    contact_number2 = so.mapped_column(sa.String(20), nullable=False)
    grade = so.mapped_column(sa.String(10), sa.ForeignKey('fee_structure.grade'), nullable=False)
    school_id = so.mapped_column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    
    
    fee_payments = so.relationship('FeePayment', backref='student_fee_payment', lazy=True)

class FeePayment(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, unique=True)
    method = so.mapped_column(sa.String(50), nullable=False)
    amount = so.mapped_column(sa.Float, nullable=False)
    pay_date = so.mapped_column(sa.Date, nullable=False)
    code = so.mapped_column(sa.String(20), nullable=False)
    balance = so.mapped_column(sa.Float, nullable=False)
    school_id = so.mapped_column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    student_id = so.mapped_column(sa.Integer, sa.ForeignKey('student.student_id'), nullable=False)
    
    school = so.relationship('School', backref='fee_payment_school')
    student = so.relationship('Student', backref='fee_payment_student')

class Audit(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, unique=True)
    action = so.mapped_column(sa.String(50), nullable=False)
    details = so.mapped_column(sa.String(100), nullable=False)
    timestamp = so.mapped_column(sa.DateTime, default=sa.func.current_timestamp(), nullable=False)
    
    school_id = so.mapped_column(sa.Integer, sa.ForeignKey('school.school_id'), nullable=False)
    user_id = so.mapped_column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    
    school = so.relationship('School', backref='audit_school', overlaps='audits, school_audit')
    user = so.relationship('User', backref='audit_user')

    def __repr__(self):
        return f"Audit('{self.action}', '{self.timestamp}')"
