from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from jps_erp.models import User, Student

class User_registrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=10)])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])  
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken!")
        


class Sign_inForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=10)])
    remember  = BooleanField('Remember me?')
    submit = SubmitField('Log in')

class Student_registrationForm(FlaskForm):
    full_name = StringField('full_name', validators=[DataRequired()])
    dob = StringField('dob', validators=[DataRequired()])
    gender = SelectField('gender', choices=['male', 'Male', 'female', 'Female'])
    guardian_name = StringField('guardian_name', validators=[DataRequired()])
    grade = StringField('grade', validators=[DataRequired()])

    



