
from flask import render_template, url_for, flash, redirect, request, jsonify
from jps_erp.forms import Sign_inForm, User_registrationForm, Student_registrationForm, Fee_structureForm, Additional_feeForm, TermForm, Fee_paymentForm    
from jps_erp import app, db
from jps_erp.daraja import check_transaction_status
from flask_login import login_user, current_user, UserMixin, logout_user, login_required
from jps_erp.models import User, Student, School, FeePayment, FeeStructure, AdditionalFee, Term, MpesaTransaction
import sqlalchemy as sa
from datetime import datetime
from jps_erp.utils import calculate_balance

@app.route("/", strict_slashes=False)
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

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
@login_required
def students():
    print("Debugging: Inside students route")
    current_term = Term.query.filter_by(current=True).first()
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

        return render_template('students.html', students=students, form=form, terms=terms)
    else:
        print("Debugging: No current term set")
        return "No current term set."



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
        current_term = Term.query.filter_by(current=True).first()
        current_year = datetime.now().year
        student = Student(
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


@app.route('/students/<int:student_id>/update', methods=['GET', 'POST'], strict_slashes=False)
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

@app.route('/students/<int:student_id>/inactive', methods=['POST'], strict_slashes=False)
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

        # Check if term already exists with the same name and year
        existing_term = Term.query.filter_by(name=term_name, year=term_year, school_id=current_user.school_id).first()
        
        if term_id:
            term = Term.query.get(term_id)
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
            # Unset the current term for all terms in the same year
            Term.query.filter_by(year=form.year.data, school_id=current_user.school_id).update({Term.current: False})
            db.session.commit()

        term.name = form.name.data
        term.start_date = form.start_date.data
        term.end_date = form.end_date.data
        term.year = form.year.data
        term.current = form.current.data
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
        code = form.code.data  # Get the code from the form
        cf_balance = float(form.cf_balance.data)
        school_id = current_user.school_id
        term_id = current_term.id

        # Check if student exists in the current user's school
        student = Student.query.filter_by(student_id=student_id, school_id=current_user.school_id).first()
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('new_payment'))
        try:
            balance = calculate_balance(student_id)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('new_payment'))


        if method == 'Mpesa':
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
    return render_template('new_payment.html', form=form, payments=payments)

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
    if term_filter:
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
