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

"""
class School(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contacts = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', backref='school', lazy=True)
    fee_structure = db.relationship('FeeStructure', backref='school', lazy=True)
    user_accounts = db.relationship('UserAccount', backref='school', lazy=True)
    audits = db.relationship('Audit', backref='school', lazy=True)
    #fee_payments = db.relationship('FeePayment', backref='school', lazy=True)
"""    
class Student(db.Model):
    student_id: so.Mapped[int]= so.mapped_column(primary_key=True)
    full_name: so.Mapped[str]= so.mapped_column(sa.String(100))
    dob: so.Mapped[str]= so.mapped_column(sa.String(7))
    gender: so.Mapped[str]= so.mapped_column(sa.String(10))
    guardian_name: so.Mapped[str] = so.mapped_column(sa.String(100))
    contact_number1: so.Mapped[str] = so.mapped_column(sa.String(20))
    contact_number2: so.Mapped[str] = so.mapped_column(sa.String(20))
    grade: so.Mapped[str] = so.mapped_column(sa.String(10))
    #school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    #fee_payments = db.relationship('FeePayment', backref='student', lazy=True)

    def __repr__(self):
        return f"Student('{self.full_name}', '{self.grade}')"
"""
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
    id: so.Mapped[int]= so.mapped_column(primary_key=True)
    username: so.Mapped[str]= so.mapped_column(sa.String(20), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]]= so.mapped_column(sa.String(256))
    role: so.Mapped[str]= so.mapped_column(sa.String(20))
    #school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    #audits = db.relationship('Audit', backref='user_account', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"

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