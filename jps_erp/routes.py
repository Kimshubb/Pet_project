
from flask import render_template, url_for, flash, redirect, request, jsonify, current_app, session
from jps_erp.forms import Sign_inForm, User_registrationForm, Student_registrationForm, Fee_structureForm, Additional_feeForm, TermForm, Fee_paymentForm, AssociateFeeForm, MigrateTermForm    
from jps_erp import app, db
from jps_erp.daraja import check_transaction_status
from flask_login import login_user, current_user, UserMixin, logout_user, login_required
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction, BankStatement, student_additional_fee 
import sqlalchemy as sa
from sqlalchemy import func
from datetime import datetime
from jps_erp.utils import calculate_balance, extract_transactions_from_pdf, generate_custom_student_id, process_mpesa_transaction, paid_via_method_today, get_recent_payments, active_students, inactive_students_term, inactive_students_year, paid_via_method_term, paid_via_method_year, current_year, get_current_term, get_current_term, FeeStructureNotFoundError
import os
from werkzeug.utils import secure_filename
import logging

@app.route("/", strict_slashes=False)
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'], strict_slashes=False)
def register():
    #if current_user.is_authenticated:
        #return redirect(url_for('dashboard'))
    form = User_registrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
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
                session['user_name'] = current_user.username  # Storing user name in session
                session['school_name'] = current_user.school.name 
                return redirect(url_for('dashboard'))
        else:
            print("Form validation failed", form.errors)
            flash('Form validation failed!', 'danger')
    elif request.method == 'GET':
        print("Rendering login form")
        form = Sign_inForm()
    return render_template('signin.html', form=form)

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')

@app.route('/dashboard', strict_slashes=False)
@login_required
def dashboard():
    user_name = session.get('user_name', 'User')  # Getting user name from session
    school_name = session.get('school_name', 'Your School')  # Getting school name from session
    current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
    if not current_term:
        flash('No current term set. Please set a current term.', 'info')
        return redirect(url_for('manage_terms'))

    try:
        
        school_id = current_user.school_id
        term_id = get_current_term(school_id)
        year = current_year()

        recent_payments_query = get_recent_payments(school_id, limit=10)
        total_active_students = active_students(school_id, term_id)
        total_inactive_students_term = inactive_students_term(school_id, term_id)
        total_inactive_students_year = inactive_students_year(school_id, year)

        #total_paid_via_cash_term = paid_via_method_term(school_id, term_id, 'Cash')
        #total_paid_via_cash_year = paid_via_method_year(school_id, year, 'Cash')

        #total_paid_via_bank_term = paid_via_method_term(school_id, term_id, 'Bank')
        #total_paid_via_bank_year = paid_via_method_year(school_id, year, 'Bank')

        #total_paid_via_mpesa_term = paid_via_method_term(school_id, term_id, 'Mpesa')
        #total_paid_via_mpesa_year = paid_via_method_year(school_id, year, 'Mpesa')

        total_paid_via_cash_today = paid_via_method_today(school_id, 'Cash')
        total_paid_via_bank_today = paid_via_method_today(school_id, 'Bank')
        total_paid_via_mpesa_today = paid_via_method_today(school_id, 'Mpesa')
        total_banked_today = total_paid_via_bank_today + total_paid_via_mpesa_today

        # Logging the fetched payments for debugging
        logging.debug(f"Dashboard Recent Payments: {recent_payments_query}")

        return render_template('dashboard.html', user_name=user_name, school_name=school_name, recent_payments=recent_payments_query, 
                               total_active_students=total_active_students, total_inactive_students_term=total_inactive_students_term, 
                               total_inactive_students_year=total_inactive_students_year, total_paid_via_cash_today=total_paid_via_cash_today, 
                               total_banked_today=total_banked_today
                               )
    except Exception as e:
        logging.error(f"Error fetching recent payments for dashboard: {e}")
        flash('An error occurred while fetching recent payments.', 'danger')
        return render_template('dashboard.html', user_name=user_name, school_name=school_name, recent_payments=[])


@app.route('/logout', strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for('home'))
    #return render_template('logout.html')

@app.route('/students', methods=['GET'], strict_slashes=False)
@login_required
def students():
    print("Debugging: Inside students route")
    current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
    if current_term:
        print("Debugging: Current term found")
        grade_filter = request.args.get('grade', 'all')
        print("Debugging: Grade filter value:", grade_filter)  # Add this line to check the grade filter value

        # Print the grades stored in the database for comparison
        db_grades = [student.grade for student in Student.query.filter_by(current_term_id=current_term.id).all()]
        
        print("Debugging: Grades stored in the database:", db_grades)

        term_filter = request.args.get('term', 'all')
        #year_filter = request.args.get('year', 'all')

        query = Student.query.filter_by(current_term_id=current_term.id, school_id=current_user.school_id)

        if grade_filter != 'all':
            print("Debugging: Applying grade filter")
            query = query.filter_by(grade=grade_filter)
        if term_filter != 'all':
            print("Debugging: Applying term filter")
            query = query.filter_by(current_term_id=term_filter)
        

        students = query.all()
        form = Student_registrationForm()
        terms = Term.query.filter_by(school_id=current_user.school_id).all()  # Get all terms for the term dropdown
        # Get all additional fees for the current school
        additional_fees = AdditionalFee.query.filter_by(school_id=current_user.school_id).all()
        associate_fee_form = AssociateFeeForm()

        return render_template('students.html', students=students, form=form, terms=terms, additional_fees=additional_fees, associate_fee_form=associate_fee_form)
    else:
        print("Debugging: No current term set")
        return redirect(url_for('manage_terms'))    



@app.route('/students/add', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def new_student():
    print("Debugging: Inside new_student route")
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    form = Student_registrationForm()
    print("Debugging: Form data:", form.data)

    if form.validate_on_submit():
        print("Debugging: Form submitted")
        current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
        current_year = datetime.now().year

        school = School.query.get(current_user.school_id)
        student_id = generate_custom_student_id(school.name, current_user.school_id)
        print("Debugging: Custom student ID:", student_id)

        student = Student(
            student_id=student_id,
            full_name=form.full_name.data, 
            dob=form.dob.data,
            gender=form.gender.data,
            guardian_name=form.guardian_name.data,
            contact_number1=form.contact_number1.data,
            contact_number2=form.contact_number2.data,
            grade=form.grade.data,
            school_id=current_user.school_id,
            year=current_year,
            current_term_id=current_term.id,
            active=True
        )
        db.session.add(student)
        db.session.commit()
        flash('Student successfully registered!', 'success')
        return redirect(url_for('students'))
    else:
        print("Debugging: Form validation failed", form.errors)
        flash('Form validation failed!', 'danger')

    grade_filter = request.args.get('grade', 'all')
    term_filter = request.args.get('term', 'all')

    query = Student.query

    if grade_filter != 'all':
        query = query.filter_by(grade=grade_filter)
    if term_filter != 'all':
        query = query.filter_by(current_term_id=term_filter)

    students = query.all()
    terms = Term.query.all()  # Get all terms for the term dropdown

    return render_template('students.html', students=students, form=form, terms=terms)


@app.route('/students/<string:student_id>/update', methods=['GET', 'POST'], strict_slashes=False)
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = Student_registrationForm(obj=student)
    if form.validate_on_submit():
        print("Debugging: Form validated successfully")
        student.full_name = form.full_name.data
        student.dob = form.dob.data.strftime('%Y-%m-%d')
        student.gender = form.gender.data
        student.guardian_name = form.guardian_name.data
        student.contact_number1 = form.contact_number1.data
        student.contact_number2 = form.contact_number2.data
        student.grade = form.grade.data
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('students'))
    elif request.method == 'GET':
        print("Debugging: GET request to update student")
        form.full_name.data = student.full_name
        if student.dob:
            form.dob.data = datetime.strptime(student.dob, '%Y-%m-%d')
        form.gender.data = student.gender
        form.guardian_name.data = student.guardian_name 
        form.grade.data = student.grade 
    return render_template('update_student.html', form=form, student=student)

@app.route('/students/<string:student_id>/inactive', methods=['POST'], strict_slashes=False)
@login_required
def toggle_student_status(student_id):
    student = Student.query.get_or_404(student_id)
    student.active = not student.active
    student.left_date = datetime.today() if not student.active else None
    db.session.commit()
    status = 'active' if student.active else 'inactive'
    flash(f'Student marked as {status}!', 'success')
    return redirect(url_for('students'))

@app.route('/terms', methods=['GET', 'POST'])
@login_required
def manage_terms():
    form = TermForm()
    if form.validate_on_submit():
        term_id = request.form.get('term_id')
        term_name = form.name.data
        term_year = form.year.data

        # Check if term already exists with the same name and year for the current school
        existing_term = Term.query.filter_by(name=term_name, year=term_year, school_id=current_user.school_id).first()
        
        if term_id:
            term = Term.query.filter_by(id=term_id, school_id=current_user.school_id).first()
            if not term:
                flash('Term not found.', 'danger')
                return redirect(url_for('manage_terms'))
        else:
            if existing_term:
                flash(f"Term already exists for the year {term_year}.", 'danger')
                return redirect(url_for('manage_terms'))
            term = Term(school_id=current_user.school_id)
            db.session.add(term)

        if form.current.data:
            # Unset the current term for all terms in the same year and school
            Term.query.filter_by(year=form.year.data, school_id=current_user.school_id).update({Term.current: False})
            db.session.commit()

        term.name = form.name.data
        term.start_date = form.start_date.data
        term.end_date = form.end_date.data
        term.year = form.year.data
        term.current = form.current.data
        term.school_id = current_user.school_id
        db.session.commit()
        
        flash('Term has been added/updated!', 'success')
        return redirect(url_for('manage_terms'))

    terms = Term.query.filter_by(school_id=current_user.school_id).all()
    return render_template('manage_terms.html', form=form, terms=terms)


@app.route('/delete_student', methods=['POST'], strict_slashes=False)
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student successfully deleted!', 'success')
    return redirect(url_for('students'))

"""
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
        pay_date = datetime.strptime(form.date.data, '%m/%d/%Y')
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
"""
"""
@app.route('/new_payment', methods=['POST', 'GET'])
@login_required
def new_payment():
    if not current_user.is_authenticated:
        print("Debug: User is not authenticated. Redirecting to login.")
        return redirect(url_for('login'))
    print(f"Debug: User is authenticated. User ID: {current_user.id}, Username: {current_user.username}")
    
    form = Fee_paymentForm()
    print(form.errors)
    if form.is_submitted():
        print("submitted")

    if form.validate():
        print("valid")

    print(form.errors)

    if form.validate_on_submit():
        current_term = Term.query.filter_by(current=True).first()
        print(f"Debug: current term found: {current_term}")

        pay_date = datetime.today
        student_id = form.student_id.data
        method = form.method.data
        amount = float(form.amount.data)
        code =urn redirect(url_for('new_payment'))
        try:
            balance = calculate_balance(student_id)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('new_payment'))


        if method  form.code.data  # Get the code from the form
        cf_balance = float(form.cf_balance.data)
        school_id = current_user.school_id
        term_id = current_term.id

        # Check if student exists in the current user's school
        student = Student.query.filter_by(student_id=student_id, school_id=current_user.school_id).first()
        if not student:
            flash('Student not found', 'danger')
            ret== 'Mpesa':
            # Check if the Mpesa transaction code has already been used
            mpesa_transaction = MpesaTransaction.query.filter_by(code=code).first()
            if mpesa_transaction and mpesa_transaction.used:
                flash('Mpesa transaction code has already been used.', 'danger')
                return redirect(url_for('new_payment'))

            # Verify the Mpesa transaction using the code from the form
            if not check_transaction_status(code):
                flash('Mpesa transaction verification failed. Please try again.', 'danger')
                return redirect(url_for('new_payment'))

            # Mark the transaction code as used
            if mpesa_transaction:
                mpesa_transaction.used = True
            else:
                mpesa_transaction = MpesaTransaction(code=code, verified=True, used=True)
            db.session.add(mpesa_transaction)
            db.session.commit()

        new_payment = FeePayment(
            method=method,
            amount=amount,
            code=code,
            balance=balance,  # This should be recalculated correctly
            cf_balance=0,
            school_id=school_id,
            student_id=student.student_id,
            pay_date=pay_date,
            term_id=term_id
        )

        try:
            db.session.add(new_payment)
            db.session.commit()
            flash('Payment added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding payment: {str(e)}', 'danger')

        receipt_data = {
            'student': student,
            'payment': new_payment
        }
        return render_template('receipt.html', receipt=receipt_data)

    payments = FeePayment.query.filter_by(school_id=current_user.school_id).all()
    return render_template('new_payment.html', form=form, payments=payments)"""

@app.route('/search_student')
@login_required
def search_student():
    query = request.args.get('q', '')
    if query:
        students = Student.query.filter(Student.full_name.ilike(f'%{query}%'), Student.school_id == current_user.school_id).all()
        suggestions = []
        for student in students:
            # Assuming there is a method or attribute to get the current term for the student
            current_term = (
                db.session.query(Term)
                .join(Student, Student.current_term_id == Term.id)
                .filter(Student.student_id == student.student_id, Term.current == True)
                .first()
            )
            term_id = current_term.id if current_term else None
            suggestions.append({'id': student.student_id, 'name': student.full_name, 'term_id': term_id})
        return jsonify(suggestions)
    return jsonify([])

"""
@app.route('/fee_structure', methods=['GET', 'POST'])
@login_required
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
            

            # Process additional fees//
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
            return redirect(url_for('payments'))//
        except Exception as e:
            # Log the error for debugging purposes
            print(f'Error occurred: {e}')
            flash(f'An error occurred: {str(e)}', 'danger')
            # Redirect to the form page or display an error page
            return redirect(url_for('fee_structure'))  # Redirect to the form page
    return render_template('fee_structure.html', form=form)
"""
@app.route('/fee_structure', methods=['GET', 'POST'])
@login_required
def manage_fee_structure():
    form = Fee_structureForm()
    form.term_id.choices = [(term.id, f"{term.name} {term.year}") for term in Term.query.filter_by(school_id=current_user.school_id).all()]
    print(form.errors)

    if form.is_submitted():
        print("submitted")

    if form.validate():
        print("valid")

    print(form.errors)
    term_filter = request.args.get('term', 'all')
    grade_filter = request.args.get('grade', 'all')

    print("Debug: Entered manage_fee_structure route")
    print(f"Debug: term_filter = {term_filter}")

    if form.validate_on_submit():
        fee_structure_id = request.form.get('fee_structure_id')
        grade = form.grade.data
        term_id = form.term_id.data  # term ID from the form
        tuition_fee = float(form.tuition_fee.data)
        ass_books = float(form.ass_books.data)
        diary_fee = float(form.diary_fee.data)
        activity_fee = float(form.activity_fee.data)
        others = float(form.others.data)


        print(f"Debug: Form validated. fee_structure_id = {fee_structure_id}, grade = {grade}, term_id = {term_id}")
        print(f"Debug: tuition_fee = {tuition_fee}, ass_books = {ass_books}, diary_fee = {diary_fee}, activity_fee = {activity_fee}, others = {others}")

        term = Term.query.get(term_id)  # Get the Term instance from the ID
        print(f"Debug: Retrieved term = {term}")

        if fee_structure_id:
            # Update existing fee structure
            fee_structure = FeeStructure.query.get(fee_structure_id)
            if not fee_structure:
                flash('Fee structure not found.', 'danger')
                print("Debug: Fee structure not found.")
                return redirect(url_for('manage_fee_structure'))
            print("Debug: Updating existing fee structure")
            fee_structure.grade = grade
            fee_structure.term = term
            fee_structure.tuition_fee = tuition_fee
            fee_structure.ass_books = ass_books
            fee_structure.diary_fee = diary_fee
            fee_structure.activity_fee = activity_fee
            fee_structure.others = others
        else:
            
            # Create new fee structure
            print("Debug: Creating new fee structure")
            existing_fee_structure = FeeStructure.query.filter_by(grade=grade, term=term, school_id=current_user.school_id).first()
            if existing_fee_structure:
                print("Debug: Fee structure for this grade and term already exists.")
                flash('Fee structure for this grade and term already exists.', 'danger')
                return redirect(url_for('manage_fee_structure'))

            fee_structure = FeeStructure(
                grade=grade, 
                term_id=term_id, 
                tuition_fee=tuition_fee, 
                ass_books=ass_books,
                diary_fee=diary_fee, 
                activity_fee=activity_fee, 
                others=others,
                school_id=current_user.school_id
            )
            db.session.add(fee_structure)
        
        db.session.commit()
        flash('Fee structure has been added/updated!', 'success')
        return redirect(url_for('manage_fee_structure'))

    fee_structures_query = FeeStructure.query.filter_by(school_id=current_user.school_id)
    if grade_filter != 'all':
        print("Debug: Applying grade filter")
        fee_structures_query = fee_structures_query.filter_by(grade=grade_filter)
    if term_filter != 'all':
        fee_structures_query = fee_structures_query.filter_by(term_id=term_filter)
    fee_structures = fee_structures_query.all()
    print(f"Debug: Retrieved fee_structures = {fee_structures}")

    terms = Term.query.filter_by(school_id=current_user.school_id).all()
    grades = db.session.query(FeeStructure.grade).distinct().all()
    grades = [grades[0] for grade in grades]
    print(f"Debug: Retrieved terms = {terms}")

    return render_template('fee_structure.html', form=form, fee_structures=fee_structures, terms=terms, grades=grades)



@app.route('/settings/additional_fees', methods=['GET', 'POST'])
def manage_additional_fees():
    form = Additional_feeForm()
    if form.validate_on_submit():
        fee_name = form.fee_name.data
        amount = form.amount.data
        school_id = current_user.school_id

        # Check if the fee already exists
        additional_fee = AdditionalFee.query.filter_by(fee_name=fee_name, school_id=school_id).first()
        if additional_fee:
            # Update the existing fee
            additional_fee.amount = amount
            flash(f'Updated {fee_name} to {amount}', 'success')
        else:
            # Add a new fee
            additional_fee = AdditionalFee(fee_name=fee_name, amount=amount, school_id=school_id)
            db.session.add(additional_fee)
            flash(f'Added {fee_name} with amount {amount}', 'success')

        db.session.commit()
        return redirect(url_for('manage_additional_fees'))

    # Load existing additional fees
    school_id = current_user.school_id # Replace with the actual school_id
    additional_fees = AdditionalFee.query.filter_by(school_id=school_id).all()
    return render_template('manage_add_fees.html', form=form, additional_fees=additional_fees)

@app.route('/student/<string:student_id>/add_fee', methods=['GET', 'POST'])
@login_required
def add_additional_fee(student_id):
    student = Student.query.get_or_404(student_id)
    form = AssociateFeeForm()
    form.additional_fee_id.choices = [(fee.id, fee.fee_name) for fee in AdditionalFee.query.filter_by(school_id=current_user.school_id).all()]

    if form.validate_on_submit():
        additional_fee_id = form.additional_fee_id.data
        # Check if the association already exists
        existing_association = db.session.query(Student).join(student_additional_fee).filter(
            student_additional_fee.c.student_id == student_id,
            student_additional_fee.c.additional_fee_id == additional_fee_id
        ).first()

        if existing_association:
            flash('This additional fee is already associated with the student.', 'warning')
        else:
            fee = AdditionalFee.query.get(additional_fee_id)
            student.additional_fees.append(fee)
            db.session.commit()
            flash('Additional fee added successfully', 'success')

        return redirect(url_for('add_additional_fee', student_id=student_id))

    # Fetch the additional fees already associated with the student
    associated_fees = student.additional_fees

    return render_template('add_additionalfee.html', student=student, form=form, associated_fees=associated_fees)

@app.route('/migrate_term', methods=['GET', 'POST'])
@login_required
def migrate_term():
    form = MigrateTermForm()
    current_term = Term.query.filter_by(school_id=current_user.school_id, current=True).first()
    
    if form.validate_on_submit():
        term_id = form.term_id.data
        new_term = Term.query.filter_by(id=term_id, school_id=current_user.school_id).first()
        
        if not new_term:
            flash('Term not found.', 'danger')
            return redirect(url_for('migrate_term'))
        
        # Migrate active students and their payments to the new term
        active_students = Student.query.filter_by(school_id=current_user.school_id, active=True).all()
        if active_students:
            for student in active_students:
                student.current_term_id = term_id
            db.session.commit()
            flash('Active students and their payments have been migrated successfully.', 'success')
        else:
            flash('No active students found.', 'info')
        return redirect(url_for('migrate_term'))

    return render_template('migrate_term.html', form=form, current_term=current_term)

@app.route('/new_payment', methods=['POST', 'GET'])
@login_required
def new_payment():
    form = Fee_paymentForm()

    logging.debug("Inside new_payment route")
    logging.debug(f"Form errors: {form.errors}")

    if form.is_submitted():
        logging.debug("Form is submitted")

    if form.validate():
        logging.debug("Form is valid")

    if form.validate_on_submit():
        current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
        if not current_term:
            flash('No current term is set. Please set a current term before making payments.', 'danger')
            return redirect(url_for('new_payment'))
        
        logging.debug(f"Current term ID: {current_term.id}")

        pay_date = datetime.today().date()
        student_id = form.student_id.data
        method = form.method.data
        amount = float(form.amount.data)
        code = form.code.data if method in ['Mpesa', 'Bank'] else None
        school_id = current_user.school_id
        term_id = current_term.id

        logging.debug(f"Payment date: {pay_date}")
        logging.debug(f"Student ID: {student_id}")
        logging.debug(f"Method: {method}")
        logging.debug(f"Amount: {amount}")
        logging.debug(f"Code: {code}")
        logging.debug(f"School ID: {school_id}")
        logging.debug(f"Term ID: {term_id}")

        student = Student.query.filter_by(student_id=student_id, school_id=school_id).first()
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('new_payment'))

        balance, cf_balance = calculate_balance(student_id)

        logging.debug(f"Current balance: {balance}")
        logging.debug(f"Carry forward balance: {cf_balance}")

        if method == 'Mpesa':
            if not process_mpesa_transaction(code, amount):
                return redirect(url_for('new_payment'))

        new_payment = FeePayment(
            method=method,
            amount=amount,
            code=code,
            balance=balance - amount,
            cf_balance=cf_balance,
            school_id=school_id,
            student_id=student.student_id,
            pay_date=pay_date,
            term_id=term_id
        )

        try:
            db.session.add(new_payment)
            db.session.commit()
            flash('Payment added successfully', 'success')
            logging.debug(f"New payment added with ID: {new_payment.id}")
            return redirect(url_for('print_receipt', student_id=student.student_id, payment_id=new_payment.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding payment: {str(e)}', 'danger')
            logging.error(f"Error adding payment: {str(e)}")

    logging.debug("Form did not validate", form.errors)
    payments = FeePayment.query.filter_by(school_id=current_user.school_id).all()
    return render_template('new_payment.html', form=form, payments=payments)

"""
@app.route('/student/<int:student_id>/receipt/<int:payment_id>', methods=['GET'])
def print_receipt(student_id, payment_id):
    student = Student.query.get_or_404(student_id)
    payment = FeePayment.query.get_or_404(payment_id)
    current_term=Term.query.filter_by(current=True, school_id=current_user.school_id).first()
    school = current_user.school


    balance, cf_balance = calculate_balance(student_id)
    
    return render_template('receipt.html', student=student, payment=payment, balance=balance, cf_balance=cf_balance, current_term=current_term, school=school)
"""
@app.route('/student_payments', methods=['GET'])
@login_required
def student_payments():
    grade_filter = request.args.get('grade', 'all')
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()

    query = Student.query.filter_by(school_id=current_user.school_id, active=True)
    if grade_filter != 'all':
        query = query.filter_by(grade=grade_filter)
    students = query.all()

    student_payment_details = []

    for student in students:
        total_paid = db.session.query(func.sum(FeePayment.amount)).filter_by(student_id=student.student_id, term_id=current_term.id).scalar() or 0.0
        try:
            balance, cf_balance = calculate_balance(student.student_id)
        except FeeStructureNotFoundError as e:
            flash(str(e), 'warning')
            return redirect(url_for('manage_fee_structure'))

        student_payment_details.append({
            'student': student,
            'cf_balance': cf_balance,
            'total_paid': total_paid,
            'balance': balance
        })

    grades = db.session.query(Student.grade).distinct().all()

    return render_template('student_payments.html', student_payment_details=student_payment_details, current_term=current_term, grades=grades, selected_grade=grade_filter)


@app.route('/student/<string:student_id>/receipt/<int:payment_id>', methods=['GET'])
@login_required
def print_receipt(student_id, payment_id):
    student = Student.query.get_or_404(student_id)
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
    school = current_user.school

    if payment_id == 0:  # Generate a fee statement instead of a single payment receipt
        payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.pay_date).all()
        total_paid = sum(payment.amount for payment in payments)
        balance, cf_balance = calculate_balance(student_id)

        return render_template('fee_statement.html', student=student, payments=payments, balance=balance, cf_balance=cf_balance, total_paid=total_paid, current_term=current_term, school=school)
    else:
        payment = FeePayment.query.get_or_404(payment_id)
        balance, cf_balance = calculate_balance(student_id)

        return render_template('receipt.html', student=student, payment=payment, balance=balance, cf_balance=cf_balance, current_term=current_term, school=school)
 
@app.route('/recent_payments', strict_slashes=False)
@login_required
def recent_payments():
    try:
        # Fetch all recent payments
        recent_payments_query = get_recent_payments(current_user.school_id, limit=None)  # No limit to get all payments

        # Logging the fetched payments for debugging
        logging.debug(f"All Recent Payments: {recent_payments_query}")

        return render_template('recent_payments.html', recent_payments=recent_payments_query)
    except Exception as e:
        logging.error(f"Error fetching all recent payments: {e}")
        flash('An error occurred while fetching recent payments.', 'danger')
        return render_template('recent_payments.html', recent_payments=[])
    
@app.route('/fee_reports', methods=['GET'])
@login_required
def fee_reports():
    grades = db.session.query(Student.grade.distinct()).all()
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()

    grade_details = []

    for grade in grades:
        grade_name = grade[0]
        
        # Query expected fees for the grade
        fee_structure = FeeStructure.query.filter_by(
            grade=grade_name,
            term_id=current_term.id,
            school_id=current_user.school_id
        ).first()

        if not fee_structure:
            continue  # Skip if fee structure not found

        # Query number of students in the grade
        total_students = db.session.query(func.count(Student.student_id)).filter_by(grade=grade_name, school_id=current_user.school_id).scalar()

        # Calculate total expected fees
        expected_fees = (
            fee_structure.tuition_fee +
            fee_structure.ass_books +
            fee_structure.diary_fee +
            fee_structure.activity_fee +
            fee_structure.others
        ) * total_students

        # Query total additional fees and number of occurrences for the grade
        additional_fees_query = db.session.query(
            AdditionalFee.fee_name,
            func.count(AdditionalFee.id)
        ).join(Student.additional_fees).filter(Student.grade == grade_name).group_by(AdditionalFee.fee_name).all()

        # Calculate total additional fees and number of occurrences
        total_additional_fees = 0.0
        additional_fee_counts = {}
        
        for fee_name, count in additional_fees_query:
            total_additional_fees += count * AdditionalFee.query.filter_by(fee_name=fee_name).first().amount
            additional_fee_counts[fee_name] = count

        # Query total fees paid for the grade
        total_fees_paid = db.session.query(func.sum(FeePayment.amount)).\
            join(Student.fee_payments).\
            filter(Student.grade == grade_name, FeePayment.term_id == current_term.id).scalar() or 0.0


        # Calculate total balance
        total_balance = expected_fees + total_additional_fees - total_fees_paid

        grade_details.append({
            'grade_name': grade_name,
            'expected_fees': expected_fees,
            'total_additional_fees': total_additional_fees,
            'additional_fee_counts': additional_fee_counts,
            'total_fees_paid': total_fees_paid,
            'total_balance': total_balance,
            'total_students': total_students
        })

    return render_template('fee_reports.html', grade_details=grade_details)
"""
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    logging.debug(f"Checking if file {filename} is allowed")
    is_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    logging.debug(f"File {filename} allowed: {is_allowed}")
    return is_allowed"""

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    print(f"Debug: Checking if file {filename} is allowed")
    is_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print(f"Debug: File {filename} allowed: {is_allowed}")
    return is_allowed


@app.route('/upload_statement', methods=['GET', 'POST'])
@login_required
def upload_statement():
    print("Debug: Inside upload_statement route")
    if request.method == 'POST':
        print("Debug: POST request detected")
        if 'file' not in request.files:
            print("Debug: No file part in request")
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        print(f"Debug: File received: {file.filename}")

        if file.filename == '':
            print("Debug: No selected file")
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            print(f"Debug: File {file.filename} is allowed")
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            print(f"Debug: Filepath set to {filepath}")

            try:
                # Ensure the upload directory exists
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    print(f"Debug: Created upload directory {upload_folder}")
                
                file.save(filepath)
                print(f"Debug: File saved to {filepath}")

                bank_statement = BankStatement(filename=filename)
                db.session.add(bank_statement)
                db.session.commit()
                print(f"Debug: Bank statement record added to database with filename {filename}")

                # Extract transaction codes from the PDF
                extracted_transactions = extract_transactions_from_pdf(filepath)
                print(f"Debug: Extracted transactions: {extracted_transactions}")

                # Store extracted transactions in session for verification
                session['extracted_transactions'] = extracted_transactions
                
                flash('File uploaded and transactions extracted successfully.', 'success')
                return redirect(url_for('verify_transactions'))
            except Exception as e:
                print(f"Debug: Exception occurred: {str(e)}")
                flash('An error occurred while processing the file.', 'danger')
                return redirect(request.url)
        else:
            print("Debug: File not allowed")
            flash('File type not allowed', 'danger')
            return redirect(request.url)

    print("Debug: GET request detected")
    return render_template('verify_transactions.html')

"""2nd one
@app.route('/upload_statement', methods=['GET', 'POST'])
@login_required
def upload_statement():
    logging.debug("Inside upload_statement route")
    if request.method == 'POST':
        logging.debug("POST request detected")
        if 'file' not in request.files:
            logging.debug("No file part in request")
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        logging.debug(f"File received: {file.filename}")

        if file.filename == '':
            logging.debug("No selected file")
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            logging.debug(f"File {file.filename} is allowed")
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            logging.debug(f"Filepath set to {filepath}")

            try:
                # Ensure the upload directory exists
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    logging.debug(f"Created upload directory {upload_folder}")
                
                file.save(filepath)
                logging.debug(f"File saved to {filepath}")

                bank_statement = BankStatement(filename=filename)
                db.session.add(bank_statement)
                db.session.commit()
                logging.debug(f"Bank statement record added to database with filename {filename}")

                # Extract transaction codes from the PDF
                extracted_transactions = extract_transactions_from_pdf(filepath)
                logging.debug(f"Extracted transactions: {extracted_transactions}")

                # Store extracted transactions in session for verification
                session['extracted_transactions'] = extracted_transactions
                
                flash('File uploaded and transactions extracted successfully.', 'success')
                return redirect(url_for('verify_transactions'))
            except Exception as e:
                logging.error(f"Exception occurred: {str(e)}")
                flash('An error occurred while processing the file.', 'danger')
                return redirect(request.url)
        else:
            logging.debug("File not allowed")
            flash('File type not allowed', 'danger')
            return redirect(request.url)

    logging.debug("GET request detected")
    return render_template('verify_transactions.html')

@app.route('/upload_statement', methods=['GET', 'POST'])
@login_required
def upload_statement():
    print("Debug: Inside upload_statement route")
    if request.method == 'POST':
        print("Debug: POST request detected")
        if 'file' not in request.files:
            print("Debug: No file part in request")
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print("Debug: No selected file")
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print(f"Debug: File {file.filename} is allowed")
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            
            # Ensure the upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file.save(filepath)
            print(f"Debug: File saved to {filepath}")

            bank_statement = BankStatement(filename=filename)
            db.session.add(bank_statement)
            db.session.commit()
            print(f"Debug: Bank statement record added to database with filename {filename}")

            # Extract transaction codes from the PDF
            extracted_transactions = extract_transactions_from_pdf(filepath)
            print(f"Debug: Extracted transactions: {extracted_transactions}")
            
            # Store extracted transactions in session for verification
            session['extracted_transactions'] = extracted_transactions
            
            flash('File uploaded and transactions extracted successfully.', 'success')
            return redirect(url_for('verify_transactions'))

    print("Debug: GET request detected")
    return render_template('verify_transactions.html')
"""
@app.route('/verify_transactions', methods=['GET', 'POST'])
@login_required
def verify_transactions():
    print("Debug: Inside verify_transactions route")

    # Retrieve extracted transactions from the session
    extracted_transactions = session.get('extracted_transactions', [])
    print(f"Debug: Extracted transactions from session: {extracted_transactions}")

    if request.method == 'POST':
        print("Debug: POST request detected for verification")

        # Retrieve all unverified transactions from the database
        unverified_db_transactions = MpesaTransaction.query.filter_by(verified=False).all()
        print(f"Debug: Unverified transactions in DB: {unverified_db_transactions}")

        # Initialize counters and lists
        verified_count = 0
        unverified_transactions = []

        # Iterate over each extracted transaction
        for extracted_transaction in extracted_transactions:
            code = extracted_transaction['code']
            amount = extracted_transaction['amount']
            print(f"Debug: Verifying transaction - Code: {code}, Amount: {amount}")

            # Check if the extracted transaction matches any unverified transaction in the database
            match_found = False
            for db_transaction in unverified_db_transactions:
                if db_transaction.code == code and db_transaction.amount == amount:
                    # Mark the transaction as verified
                    db_transaction.verified = True
                    db.session.commit()
                    verified_count += 1
                    match_found = True
                    print(f"Debug: Transaction verified and updated - Code: {code}, Amount: {amount}")
                    break

            if not match_found:
                # Check for the student details related to the unverified transaction
                student_transaction = MpesaTransaction.query.filter_by(code=code).first()
                student = Student.query.get(student_transaction.student_id) if student_transaction else None
                unverified_transactions.append({
                    'code': code,
                    'amount': amount,
                    'student': student.full_name if student else 'Unknown Student'
                })
                print(f"Debug: Unverified transaction - Code: {code}, Amount: {amount}, Student: {student.full_name if student else 'Unknown Student'}")

        print(f"Debug: Verification complete - Verified Count: {verified_count}, Unverified Transactions: {unverified_transactions}")
        return render_template('verify_transactions.html', verified_count=verified_count, unverified_transactions=unverified_transactions)

    print("Debug: GET request detected for verification")
    return render_template('verify_transactions.html')