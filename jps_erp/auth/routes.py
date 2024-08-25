from . import auth_bp
from flask import render_template, url_for, flash, redirect, request, session, jsonify
from jps_erp import db
from jps_erp.models import User, School
from jps_erp.utils import register_user, send_password_reset_email, send_async_email_task
from jps_erp.forms import User_registrationForm, Sign_inForm, PasswordResetRequestForm, ResetPasswordForm  
from flask_login import login_user, current_user, logout_user  
import sqlalchemy as sa
from redis import Redis
from flask import current_app as app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



@auth_bp.route("/", strict_slashes=False)
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return render_template ('main/index.html')

@auth_bp.route('/autocomplete_school', methods=['GET'])
def autocomplete_school():
    search_term = request.args.get('q', '')
    results = School.query.filter(School.name.ilike(f'%{search_term}%')).all()
    school_names = [school.name for school in results]
    return jsonify(school_names)

@auth_bp.route('/get_school_contacts', methods=['GET'])
def get_school_contacts():
    school_name = request.args.get('school_name')
    school = School.query.filter_by(name=school_name).first()
    if school:
        return jsonify({'contacts': school.contacts})
    else:
        return jsonify({'contacts': None})

@auth_bp.route("/register", methods=['GET', 'POST'], strict_slashes=False)
def register():
    form = User_registrationForm()
    if form.validate_on_submit():
        new_user, error = register_user(form)
        if error:
            flash(error, 'danger')
            return redirect(url_for('auth.register'))

        # Send welcome email asynchronously
        send_async_email_task.delay(
            subject="Welcome to the Platform",
            recipient=form.username.data,
            body="Thank you for registering!"
        )

        flash(f'Account successfully created for {form.username.data}!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_password_token()
            send_password_reset_email(user, token)  # Send the reset email
        flash('Check your email for instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

limiter = Limiter(key_func=get_remote_address, app=app)
@auth_bp.route("/login", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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
