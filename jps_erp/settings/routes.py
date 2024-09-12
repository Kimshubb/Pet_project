from . import settings_bp
from flask import render_template, redirect, url_for, flash, request
from jps_erp import db
from jps_erp.models import Term, FeeStructure, AdditionalFee, Grade, Stream, Student
from jps_erp.forms import TermForm, Fee_structureForm, Additional_feeForm, MigrateTermForm, GradeConfigurationForm
from flask_login import login_required, current_user

@settings_bp.context_processor
def utility_processor():
    return dict(str=str)


@settings_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings/settings.html')


@settings_bp.route('/terms', methods=['GET', 'POST'])
@login_required
def manage_terms():
    form = TermForm()

    if form.validate_on_submit():
        term_id = request.form.get('term_id')
        term_name = form.name.data
        term_year = form.year.data

        # Check if the term already exists with the same name and year for the current school
        existing_term = Term.query.filter_by(name=term_name, year=term_year, school_id=current_user.school_id).first()

        if term_id:
            # If term_id is provided, update the existing term
            term = Term.query.get(term_id)
            if not term:
                flash('Term not found.', 'danger')
                return redirect(url_for('settings.manage_terms'))
        else:
            # If no term_id, create a new term, but ensure it doesn't already exist for the current school and year
            if existing_term:
                flash(f"Term {term_name} already exists for the year {term_year}.", 'danger')
                return redirect(url_for('settings.manage_terms'))
            term = Term(school_id=current_user.school_id)
            db.session.add(term)

        # If the term is marked as current, unset the current flag for all other terms in the same school
        if form.current.data:
            Term.query.filter_by(school_id=current_user.school_id).update({Term.current: False})
            db.session.commit()

        # Update or set the term fields
        term.name = term_name
        term.start_date = form.start_date.data
        term.end_date = form.end_date.data
        term.year = form.year.data
        term.current = form.current.data
        db.session.commit()
        
        flash('Term has been added/updated successfully!', 'success')
        return redirect(url_for('settings.manage_terms'))

    # Retrieve and display all terms specific to the current user's school
    terms = Term.query.filter_by(school_id=current_user.school_id).all()
    return render_template('settings/manage_terms.html', form=form, terms=terms)

@settings_bp.route('/fee_structure', methods=['GET', 'POST'])
@login_required
def manage_fee_structure():
    form = Fee_structureForm()
    form.term_id.choices = [(term.id, f"{term.name} {term.year}") for term in Term.query.filter_by(school_id=current_user.school_id).all()]
    form.grade.choices = [(grade.id, grade.name) for grade in Grade.query.filter_by(school_id=current_user.school_id).all()]

    print("Debug: Entered manage_fee_structure route")
    print(f"Debug: form errors = {form.errors}")

    if form.validate_on_submit():
        fee_structure_id = request.form.get('fee_structure_id')
        grade_id = form.grade.data
        term_id = form.term_id.data
        tuition_fee = float(form.tuition_fee.data)
        ass_books = float(form.ass_books.data)
        diary_fee = float(form.diary_fee.data)
        activity_fee = float(form.activity_fee.data)
        others = float(form.others.data)

        print(f"Debug: Form validated. fee_structure_id = {fee_structure_id}, grade_id = {grade_id}, term_id = {term_id}")
        print(f"Debug: tuition_fee = {tuition_fee}, ass_books = {ass_books}, diary_fee = {diary_fee}, activity_fee = {activity_fee}, others = {others}")

        term = Term.query.get(term_id)
        grade = Grade.query.get(grade_id)

        if not term or not grade:
            flash('Invalid term or grade.', 'danger')
            print("Debug: Invalid term or grade.")
            return redirect(url_for('settings.manage_fee_structure'))

        if fee_structure_id:
            # Update existing fee structure
            fee_structure = FeeStructure.query.get(fee_structure_id)
            if not fee_structure:
                flash('Fee structure not found.', 'danger')
                print("Debug: Fee structure not found.")
                return redirect(url_for('settings.manage_fee_structure'))

            print("Debug: Updating existing fee structure")
            fee_structure.grade_id = grade_id
            fee_structure.term_id = term_id
            fee_structure.tuition_fee = tuition_fee
            fee_structure.ass_books = ass_books
            fee_structure.diary_fee = diary_fee
            fee_structure.activity_fee = activity_fee
            fee_structure.others = others
        else:
            # Create new fee structure
            current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()
            print("Debug: Creating new fee structure")
            existing_fee_structure = FeeStructure.query.filter_by(grade_id=grade_id, term_id=current_term.id, school_id=current_user.school_id).first()
            if existing_fee_structure:
                print("Debug: Fee structure for this grade and term already exists.")
                flash('Fee structure for this grade and term already exists.', 'danger')
                return redirect(url_for('settings.manage_fee_structure'))

            fee_structure = FeeStructure(
                grade_id=grade_id,
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
        return redirect(url_for('settings.manage_fee_structure'))

    # Fetch grades, terms, and fee structures for rendering the template
    term_filter = request.args.get('term', 'all')
    grade_filter = request.args.get('grade', 'all')

    query = FeeStructure.query.filter_by(school_id=current_user.school_id)
    if grade_filter != 'all':
        query = query.filter_by(grade_id=grade_filter)
    if term_filter != 'all':
        query = query.filter_by(term_id=term_filter)

    fee_structures = query.all()
    terms = Term.query.filter_by(school_id=current_user.school_id).all()
    grades = Grade.query.filter_by(school_id=current_user.school_id).all()

    return render_template('settings/fee_structure.html', form=form, fee_structures=fee_structures, terms=terms, grades=grades)


@settings_bp.route('/settings/additional_fees', methods=['GET', 'POST'])
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
        return redirect(url_for('settings.manage_additional_fees'))

    # Load existing additional fees
    school_id = current_user.school_id # Replace with the actual school_id
    additional_fees = AdditionalFee.query.filter_by(school_id=school_id).all()
    return render_template('settings/manage_add_fees.html', form=form, additional_fees=additional_fees)


@settings_bp.route('/migrate_term', methods=['GET', 'POST'])
@login_required
def migrate_term():
    form = MigrateTermForm()

    # Fetch all terms for the current user's school
    terms = Term.query.filter_by(school_id=current_user.school_id).all()

    # Populate the term_id choices with terms specific to the school
    form.term_id.choices = [(term.id, f"{term.name} ({term.year})") for term in terms]
    
    current_term = Term.query.filter_by(current=True, school_id=current_user.school_id).first()

    if form.validate_on_submit():
        term_id = form.term_id.data
        new_term = Term.query.filter_by(id=term_id, school_id=current_user.school_id).first_or_404()
        
        # Unset the current flag for the existing term
        if current_term:
            current_term.current = False
        
        # Set the new term as the current term
        new_term.current = True
        
        # Migrate active students to the new term
        active_students = Student.query.filter_by(school_id=current_user.school_id, active=True).all()
        for student in active_students:
            student.current_term_id = new_term.id

        # Commit changes to the database
        db.session.commit()
        
        flash('Active students and their payments have been migrated successfully.', 'success')
        return redirect(url_for('settings.migrate_term'))

    return render_template('settings/migrate_term.html', form=form, current_term=current_term, terms=terms)


@settings_bp.route('/configure_grades', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def configure_grades():
    form = GradeConfigurationForm()

    if form.validate_on_submit():
        print("Debugging: Form grades data:", form.grades.data)
        for grade_name in form.grades.data:
            grade = Grade.query.filter_by(name=grade_name, school_id=current_user.school_id).first()
            if not grade:
                print(f"Adding new grade: {grade_name}")
                grade = Grade(name=grade_name, school_id=current_user.school_id)
                db.session.add(grade)
                db.session.commit()  # Commit to get grade.id for stream relationships
            print(f"Debugging: Existing grade - ID: {grade.id}, Name: {grade.name}")
            existing_streams = {stream.name: stream for stream in grade.streams}
            print(f"Debugging: Existing streams for grade '{grade.name}': {[stream.name for stream in grade.streams]}")
            for stream_form in form.streams:
                stream_name = stream_form.stream_name.data
                if stream_name not in existing_streams:
                    print(f"Debugging: Adding new stream '{stream_name}' to grade '{grade_name}'")
                    stream = Stream(name=stream_name, grade_id=grade.id)
                    db.session.add(stream)

        db.session.commit()
        flash('Grades and Streams successfully configured!', 'success')
        return redirect(url_for('settings.configure_grades'))
    else:
        print("Debugging: Form validation failed", form.errors)
        flash('GradesForm validation failed! Please check the entered data.', 'danger')

    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    print("Debugging: Retrieved grades from database:")
    for grade in grades:
        print(f"Debugging: Grade - ID: {grade.id}, Name: {grade.name}")
        streams = [stream.name for stream in grade.streams]
        print(f"Debugging: Streams for grade '{grade.name}': {streams}")
    return render_template('settings/configure_grades.html', form=form, grades=grades)