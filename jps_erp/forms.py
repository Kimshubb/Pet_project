from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, DecimalField, HiddenField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from jps_erp.models import User, Student
from jps_erp import db
import sqlalchemy as sa


class User_registrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=256)])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])
    school_name = StringField('school_name', validators=[DataRequired()])
    school_contacts = StringField('school_contacts', validators=[DataRequired()])  
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
    grade = SelectField('Grade', choices=[('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
                                          ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
                                          ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6')], validators=[DataRequired()])
    submit = SubmitField('Add Student')

    def validate_phone_number(self, contact_number1):
        student = db.session.scalar(sa.select(Student).where(Student.contact_number1 == contact_number1.data))
        if student is not None:
            raise ValidationError("Student with this contact number already exists!")

class Fee_paymentForm(FlaskForm):
    student_name = StringField('student_name', validators=[DataRequired()])
    student_id = HiddenField('student_id', validators=[DataRequired()])
    method = SelectField('method', choices=[ 'Cash', 'Mpesa', 'Cheque'], validators=[DataRequired()])
    amount = DecimalField('amount', validators=[DataRequired()])
    pay_date = StringField('pay_date', validators=[DataRequired()])
    code = StringField('code', validators=[DataRequired()])
    submit = SubmitField('Pay Fees')

#class Additional_feeForm(FlaskForm):
    #fee_name = StringField('Fee Name', validators=[DataRequired()])
    #payable_amount = FloatField('Amount', validators=[DataRequired()])

class Fee_structureForm(FlaskForm):
    grade = SelectField('Grade', choices=[('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
                                          ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
                                          ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6')], validators=[DataRequired()])
    tuition_fee = FloatField('Tuition Fee', validators=[DataRequired()])
    ass_books = FloatField('Assessment Books', validators=[DataRequired()])
    diary_fee = FloatField('Diary Fee', validators=[DataRequired()])
    activity_fee = FloatField('Activity Fee', validators=[DataRequired()])
    others = FloatField('Other Fees', validators=[DataRequired()])
    #additional_fees = FieldList(FormField(Additional_feeForm), min_entries=1, max_entries=10)
    submit = SubmitField('Save')