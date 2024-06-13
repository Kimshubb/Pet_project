from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, FloatField, FieldList, FormField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee
from jps_erp import db
import sqlalchemy as sa


class User_registrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    school_name = StringField('school_name', validators=[DataRequired()])
    school_contacts = StringField('school_contacts', validators=[DataRequired()])
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
    dob = DateField('dob', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('gender', choices=[('male', 'Male'), ('female', 'Female')])
    guardian_name = StringField('guardian_name', validators=[DataRequired()])
    contact_number1 = StringField('contact_number1', validators=[DataRequired()])
    contact_number2 = StringField('contact_number2', validators=[DataRequired()])
    grade = SelectField('Grade', choices=[('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
                                          ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
                                          ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6')], validators=[DataRequired()])
    submit = SubmitField('Add Student')

    #def validate_phone_number(self, contact_number1):
        #student = db.session.scalar(sa.select(Student).where(Student.contact_number1 == contact_number1.data))
        #if student is not None:
            #raise ValidationError("Student with this contact number already exists!")
        
class TermForm(FlaskForm):
    name = SelectField('Name', choices=[('Term 1', 'Term 1'), ('Term 2', 'Term 2'), ('Term 3', 'Term 3')], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    current = BooleanField('Current')
    submit = SubmitField('Submit')

class Fee_paymentForm(FlaskForm):
    student_id = IntegerField('Student ID', validators=[DataRequired()])
    student_name = StringField('Student Name', validators=[DataRequired()])
    method = SelectField('Method', choices=[('Cash', 'Cash'), ('Bank', 'Bank'), ('Mpesa', 'Mpesa')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    pay_date = DateField('Pay Date', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired()])
    balance = FloatField('Balance', validators=[DataRequired()])
    cf_balance = FloatField('Carry Forward Balance', default=0.0)
    school_id = IntegerField('School ID', validators=[DataRequired()])
    term_id = IntegerField('Term ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class Fee_structureForm(FlaskForm):
    grade = SelectField('Grade', choices=[('Playgroup', 'Playgroup'), ('PP1', 'PP1'), ('PP2', 'PP2'),
                                          ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
                                          ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6')], validators=[DataRequired()])
    term = SelectField('Term', choices=[('Term 1', 'Term 1'), ('Term 2', 'Term 2'), ('Term 3', 'Term 3')], validators=[DataRequired()])
    tuition_fee = FloatField('Tuition Fee', validators=[DataRequired()])
    ass_books = FloatField('Assessment Books', validators=[DataRequired()])
    diary_fee = FloatField('Diary Fee', validators=[DataRequired()])
    activity_fee = FloatField('Activity Fee', validators=[DataRequired()])
    others = FloatField('Other Fees', validators=[DataRequired()])
    
    #additional_fees = FieldList(FormField(Additional_feeForm), min_entries=1, max_entries=10)
    submit = SubmitField('Save')

class Additional_feeForm(FlaskForm):
    fee_name = StringField('Fee Name', validators=[DataRequired()])
    amount = FloatField('Amount', default=0.0)
    submit = SubmitField('Add/Update Fee')