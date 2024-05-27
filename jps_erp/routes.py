
from flask import render_template, url_for, flash, redirect, request, jsonify
from jps_erp.forms import Sign_inForm, User_registrationForm, Student_registrationForm, Fee_paymentForm, Fee_structureForm 
from jps_erp import app, db
from flask_login import login_user, current_user, UserMixin, logout_user
from jps_erp.models import User, Student, FeeStructure, FeePayment, School
import sqlalchemy as sa
from sqlalchemy import or_
from flask_wtf import csrf
from datetime import datetime


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
            new_school = School(name=form.school_name.data, contacts=form.school_contacts.data)

            db.session.add(new_school)
            db.session.commit()

            new_user = User(username=form.username.data, role=form.role.data, school_id=new_school.school_id)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
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
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    grade_filter = request.args.get('grade')
    if grade_filter == 'all':
        students = Student.query.filter_by(school_id=current_user.school_id).all()
    else:
        students = Student.query.filter_by(school_id=current_user.school_id, grade=grade_filter).all()
    form = Student_registrationForm()
    return render_template('students.html', students=students, form=form)

@app.route('/students/add', methods=['GET', 'POST'], strict_slashes=False)
def new_student():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = Student_registrationForm()
    if form.validate_on_submit():
        student = Student(
            full_name=form.full_name.data, 
            dob=form.dob.data,
            gender=form.gender.data,
            guardian_name=form.guardian_name.data,
            contact_number1=form.contact_number1.data,
            contact_number2=form.contact_number2.data,
            grade=form.grade.data,
            school_id=current_user.school_id    
        )
        db.session.add(student)
        db.session.commit()
        flash('Student successfully registered!', 'success')
        return redirect(url_for('students'))
    return render_template('students.html', form=form)

@app.route('/students/<int:student_id>/update', methods=['GET', 'POST'], strict_slashes=False)
def update_student(student_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    student = Student.query.filter_by(id=student_id, school_id=current_user.school_id).first_or_404()
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
    student = Student.query.filter_by(id=student_id, school_id=current_user.school_id).first_or_404()
    db.session.delete(student)
    db.session.commit()
    flash('Student successfully deleted!', 'success')
    return redirect(url_for('students'))
"""
@app.route('/search_student', methods=['GET', 'POST'], strict_slashes=False)
def search_student():
    if request.method == 'POST':
        search_query = request.form['search_query']
        school_id = current_user.school_id
        students = Student.query.filter(
            Student.student_id == school_id,
            or_(Student.full_name.like(f"%{search_query}%"),
                Student.student_id == search_query)).all()
        return render_template('search_results.html', students=students)
    return render_template('search_results.html')
    """
@app.route('/student_suggestions', methods=['GET'])
def student_suggestions():
    search_query = request.args.get('query', '')
    school_id = current_user.school_id
    suggestions = Student.query.filter(
        Student.school_id == school_id,
        or_(Student.full_name.ilike(f"%{search_query}%"),
            Student.student_id.ilike(f"%{search_query}%"))
    ).all()
    suggestion_list = [{'id': student.student_id, 'name': student.full_name} for student in suggestions]
    return jsonify(suggestion_list)


@app.route('/new_payment', methods=['POST', 'GET'])
def new_payment():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    form = Fee_paymentForm()
    print(form.errors)

    if form.is_submitted():
        print("submitted")

    if form.validate():
        print("valid")

    print(form.errors)
    if form.validate_on_submit():
        print("Processing fee structure form submission...")
        pay_date = datetime.strptime(form.pay_date.data, '%m/%d/%Y')
        student_id = form.student_id.data
        method = form.method.data
        amount = float(form.amount.data)
        code = form.code.data

        student = Student.query.filter_by(student_id=student_id, school_id=current_user.school_id).first()
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('payments'))

        new_payment = FeePayment(
            method=method,
            amount=amount,
            code=code,
            balance=0,  # balance will be recalculated on the next load
            school_id=student.school_id,
            student_id=student.student_id,
            pay_date=pay_date
        )

        db.session.add(new_payment)
        db.session.commit()
        flash('Payment added successfully', 'success')
        return redirect(url_for('payments'))

    return render_template('new_payment.html', form=form, payments=FeePayment.query.filter_by(school_id=current_user.school_id).all())

@app.route('/fee_statement/<int:student_id>')
def fee_statement(student_id):
    student = Student.query.filter_by(student_id=student_id, school_id=current_user.school_id).first_or_404()
    payments = FeePayment.query.filter_by(student_id=student_id, school_id=current_user.school_id).all()
    return render_template('fees_statement.html', student=student, payments=payments)

@app.route('/fee_structure', methods=['GET', 'POST'])
def fee_structure():
    form = Fee_structureForm()
    print(form.errors)

    if form.is_submitted():
        print("submitted")

    if form.validate():
        print("valid")

    print(form.errors)
    if form.validate_on_submit():
        #print(Fee_structureForm.errors)
        print("Processing fee structure form submission...")
        
        try:
            # Extract form data
            grade = form.grade.data
            tuition_fee = float(form.tuition_fee.data)
            ass_books = float(form.ass_books.data)
            diary_fee = float(form.diary_fee.data)
            activity_fee = float(form.activity_fee.data)
            others = float(form.others.data)
            print("Processing fee structure form submission...")

            # Check if fee structure already exists for this grade and school
            existing_fee_structure = FeeStructure.query.filter_by(grade=grade, school_id=current_user.school_id).first()
            if existing_fee_structure:
                flash('Fee structure for this grade already exists', 'warning')
                return redirect(url_for('payments'))

            # Create FeeStructure object
            fee_structure = FeeStructure(grade=grade, tuition_fee=tuition_fee, ass_books=ass_books,
                                         diary_fee=diary_fee, activity_fee=activity_fee, others=others,
                                         school_id=current_user.school_id)
            db.session.add(fee_structure)
            db.session.commit()
            """

            # Process additional fees
            for additional_fee_entry in form.additional_fees.entries:
                additional_fee_form = Additional_feeForm(obj=additional_fee_entry)
                if additional_fee_form.validate():
                    fee_name = additional_fee_form.fee_name.data
                    payable_amount = float(additional_fee_form.payable_amount.data)
                    additional_fee = AdditionalFee(fee_name=fee_name, payable_amount=payable_amount, fee_structure_grade=fee_structure.grade)
                    db.session.add(additional_fee)
                else:
                    # Log validation errors for additional fees
                    flash('Validation error for additional fee', 'danger')

            # Commit database session
            db.session.commit()

            flash('Fee structure saved successfully', 'success')
            return redirect(url_for('payments'))"""
        except Exception as e:
            # Log the error for debugging purposes
            print(f'Error occurred: {e}')
            flash(f'An error occurred: {str(e)}', 'danger')
            # Redirect to the form page or display an error page
            return redirect(url_for('fee_structure'))  # Redirect to the form page
    return render_template('fee_structure.html', form=form)


"""
@app.route('/fee_structure', methods=['GET', 'POST'])
def fee_structure():
    form = Fee_structureForm()
    if form.validate_on_submit():
        grade = form.grade.data
        tuition_fee = form.tuition_fee.data
        ass_books = form.ass_books.data
        diary_fee = form.diary_fee.data
        activity_fee = form.activity_fee.data
        others = form.others.data

        fee_structure = FeeStructure(grade=grade, tuition_fee=tuition_fee, ass_books=ass_books,
                                     diary_fee=diary_fee, activity_fee=activity_fee, others=others,
                                     school_id=current_user.school_id)  # users school
        db.session.add(fee_structure)
        db.session.commit()

        for additional_fee_entry in form.additional_fees.entries:
            additional_fee_form = Additional_feeForm(obj=additional_fee_entry)
            if additional_fee_form.validate_on_submit():
                additional_fee = AdditionalFee(
                    name=additional_fee_form.name.data,
                    amount=additional_fee_form.amount.data,
                    fee_structure_id=fee_structure.id
                )
                db.session.add(additional_fee)
                db.session.commit()
        flash('Fee structure saved successfully', 'success')
        return redirect(url_for('payments'))

    return render_template("fee_structure.html", form=form)"""

@app.route('/payments', methods=['GET'])
def payments():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    grade = request.args.get('grade', 'all')
    
    if grade == 'all':
        students = Student.query.filter_by(school_id=current_user.school_id).all()
    else:
        students = Student.query.filter_by(grade=grade, school_id=current_user.school_id).all()

   # Calculate total paid and balance for each student
    for student in students:
        fee_structure = FeeStructure.query.filter_by(school_id=student.school_id).first()
        total_fees = (fee_structure.tuition_fee + fee_structure.ass_books +
                    fee_structure.diary_fee + fee_structure.activity_fee +
                    fee_structure.others) #+
                    #sum(additional_fee.amount for additional_fee in fee_structure.additional_fees))
        total_paid = sum(payment.amount for payment in student.fee_payments)
        balance = total_fees - total_paid

        student.total_paid = total_paid
        student.balance = balance

        form = Fee_paymentForm()
        return render_template('fee_payment.html', students=students, form=form)