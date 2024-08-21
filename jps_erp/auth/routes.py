from . import auth_bp
from flask import render_template, url_for, flash, redirect, request, session
from jps_erp import db
from jps_erp.models import User, School
from jps_erp.forms import User_registrationForm, Sign_inForm
from flask_login import login_user, current_user, logout_user  
import sqlalchemy as sa


@auth_bp.route("/", strict_slashes=False)
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return render_template ('main/index.html')

@auth_bp.route("/register", methods=['GET', 'POST'], strict_slashes=False)
def register():
    #if current_user.is_authenticated:
        #return redirect(url_for('dashboard'))
    form = User_registrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create a new school
        new_school = School(name=form.school_name.data, contacts=form.school_contacts.data)
        db.session.add(new_school)
        db.session.commit()

        # Create a new user and associate it with the school
        new_user = User(
            username=form.username.data,
            role=form.role.data,
            school_id=new_school.school_id
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash(f'Account successfully created for {form.username.data}!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    print("Request method:", request.method)
    if request.method == 'POST':
        print("Processing login form submission...")
        form = Sign_inForm()
        if form.validate_on_submit():
            print("Form validation successful")
            user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
            if user is None or not user.check_password(form.password.data):
                print("Invalid username or password")
                flash('Log in unsuccessful! Incorrect username or password!', 'danger')
            else:
                print("User authenticated. Logging in...")
                login_user(user, remember=form.remember.data)
                session['user_name'] = current_user.username  # Storing user name in session
                session['school_name'] = current_user.school.name 
                return redirect(url_for('main.dashboard'))
        else:
            print("Form validation failed", form.errors)
            flash('Form validation failed!', 'danger')
    elif request.method == 'GET':
        print("Rendering login form")
        form = Sign_inForm()
    return render_template('auth/signin.html', form=form)

@auth_bp.route('/logout', strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
    #return render_template('logout.html')
