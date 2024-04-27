from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()
"""
class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contacts = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', backref='school', lazy=True)
    fee_structure = db.relationship('FeeStructure', backref='school', lazy=True)
    user_accounts = db.relationship('UserAccount', backref='school', lazy=True)
    audits = db.relationship('Audit', backref='school', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    guardian_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    fee_payments = db.relationship('FeePayment', backref='student', lazy=True)

class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    code = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
"""
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    #school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
return User

"""
class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tuition_fee = db.Column(db.Float, nullable=False)
    ass_books = db.Column(db.Float, nullable=False)
    diary_fee = db.Column(db.Float, nullable=False)
    activity_fee = db.Column(db.Float, nullable=False)
    others = db.Column(db.Float, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
"""