
from flask import render_template, url_for, flash, redirect, request
from jps_erp.forms import Sign_inForm, User_registrationForm, Student_registrationForm
from jps_erp import app, db
from flask_login import login_user, current_user, UserMixin, logout_user
from jps_erp.models import User, Student
import sqlalchemy as sa

@app.route("/", strict_slashes=False)
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'], strict_slashes=False)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = User_registrationForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None:
            user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
    
        flash(f'Account successfully created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
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
                return redirect(url_for('dashboard'))
        else:
            print("Form validation failed", form.errors)
            flash('Form validation failed!', 'danger')
    elif request.method == 'GET':
        print("Rendering login form")
        form = Sign_inForm()
    return render_template('signin.html', form=form)

"""
@app.route("/login", methods=['GET', 'POST'])
def login():
    print("Login route accessed via Request method:", request.method)
    
    if current_user.is_authenticated:
        print("Already authenticated user:", current_user)
        return redirect(url_for('dashboard'))
    form = Sign_inForm()
    if form.validate_on_submit():
        print("Form validation result:", form.validate_on_submit())
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        print("Retrieved User:", user)
        if user is None or not user.check_password(form.password.data):
            flash('Log in unsuccessful!Incorrect username or password!', 'danger')
            return redirect(url_for('login'))
        print("User authenticated sucessfully:", user)
        login_user(user, remember=form.remember.data)
        print("User logged in:", current_user.is_authenticated)
        return redirect(url_for('dashboard'))
    return render_template('signin.html', form=form)
"""
@app.route('/dashboard', strict_slashes=False)
def dashboard():

    return render_template('dashboard.html')

@app.route('/logout', strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for('login'))
    #return render_template('logout.html')

@app.route('/students', methods=['GET'], strict_slashes=False)
def students():
    grade_filter = request.args.get('grade')
    if grade_filter == 'all':
        students = Student.query.all()
    else:
        students = Student.query.filter_by(grade=grade_filter).all()
    form = Student_registrationForm()
    return render_template('students.html', students=students, form=form)

@app.route('/students/add', methods=['GET', 'POST'], strict_slashes=False)
def new_student():
    form = Student_registrationForm()
    if form.validate_on_submit():
        student = Student(
            full_name=form.full_name.data, 
            dob=form.dob.data,
            gender=form.gender.data,
            guardian_name=form.guardian_name.data,
            contact_number1=form.contact_number1.data,
            contact_number2=form.contact_number2.data,
            grade=form.grade.data
        )
        db.session.add(student)
        db.session.commit()
        flash('Student successfully registered!', 'success')
        return redirect(url_for('students'))
    return render_template('students.html', form=form)

@app.route('/students/<int:student_id>/update', methods=['GET', 'POST'], strict_slashes=False)
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = Student_registrationForm(obj=student)
    if form.validate_on_submit():
        student.full_name = form.full_name.data
        student.dob = form.dob.data 
        student.gender = form.gender.data
        student.guardian_name = form.guardian_name.data
        student.contact_number1 = form.contact_number1.data
        student.contact_number2 = form.contact_number2.data
        student.grade = form.grade.data
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('students'))
    elif request.method == 'GET':
        form.full_name.data = student.full_name
        form.dob.data = student.dob
        form.gender.data = student.gender
        form.guardian_name.data = student.guardian_name 
        form.grade.data = student.grade 
    return render_template('update_student.html', form=form, student=student)

@app.route('/delete_student', methods=['POST'], strict_slashes=False)
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student successfully deleted!', 'success')
    return redirect(url_for('students'))