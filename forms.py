from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo


class User_registrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=10)])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])  
    submit = SubmitField('Sign Up')

class Sign_inForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('accounts', 'Accounts')], validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=10)])
    remember  = BooleanField('Remember me?')
    submit = SubmitField('Log in')


