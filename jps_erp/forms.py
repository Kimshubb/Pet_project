from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from jps_erp.models import User, Student
from jps_erp import db
import sqlalchemy as sa


class User_registrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=256)])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])  
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username!")
        


class Sign_inForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=256)])
    remember  = BooleanField('remember')
    submit = SubmitField('Log in')

class Student_registrationForm(FlaskForm):
    full_name = StringField('full_name', validators=[DataRequired()])
    dob = StringField('dob', validators=[DataRequired()])
    gender = SelectField('gender', choices=['male', 'Male', 'female', 'Female'])
    guardian_name = StringField('guardian_name', validators=[DataRequired()])
    contact_number1 = StringField('contact_number1', validators=[DataRequired()])
    contact_number2 = StringField('contact_number2', validators=[DataRequired()])
    grade = StringField('grade', validators=[DataRequired()])
    submit = SubmitField('Add Student')

    def validate_phone_number(self, contact_number1):
        student = db.session.scalar(sa.select(Student).where(Student.contact_number1 == contact_number1.data))
        if student is not None:
            raise ValidationError("Student with this contact number already exists!")
