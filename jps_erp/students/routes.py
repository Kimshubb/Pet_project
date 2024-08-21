from . import students_bp
from flask import render_template, url_for, flash, redirect, request, jsonify, session
from jps_erp import db
from jps_erp.models import Student, Grade, Stream, Term, School
from jps_erp.forms import Student_registrationForm
from flask_login import login_required, current_user
from jps_erp.utils import generate_custom_student_id
from datetime import datetime


@students_bp.context_processor
def utility_processor():
    return dict(str=str)
@students_bp.route('/students', methods=['GET'])
@login_required
def students():
    page = request.args.get('page', 1, type=int)
    # Filters
    grade_filter = request.args.get('grade', 'all')
    term_filter = request.args.get('term', 'all')
    stream_filter = request.args.get('stream', 'all')

    # Base query for students
    query = Student.query.filter_by(school_id=current_user.school_id)
    
    # Apply filters
    if grade_filter != 'all':
        query = query.filter_by(grade_id=grade_filter)
    if term_filter != 'all':
        query = query.filter_by(current_term_id=term_filter)
    if stream_filter != 'all':
        query = query.filter_by(stream_id=stream_filter)

    # Retrieve students, terms, and grades for the filters and pagination of results
    per_page = 15
    students = query.paginate(page=page, per_page=per_page)

    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    terms = Term.query.filter_by(school_id=current_user.school_id).all()
    
    # To get all streams for dropdown options
    streams = Stream.query.filter(Stream.grade_id.in_([grade.id for grade in grades])).all()

    return render_template('students/students.html', students=students, grades=grades, terms=terms, streams=streams)

@students_bp.route('/students/add', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def add_student():
    form = Student_registrationForm()

    # Initialize grades from the GradeConfigurationForm choices
    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    grade_choices = [(grade.id, grade.name) for grade in grades]
    form.grade.choices = grade_choices

    # Initialize stream choices based on selected grade
    if form.grade.data:
        streams = Stream.query.filter_by(grade_id=form.grade.data).all()
        form.stream.choices = [(stream.id, stream.name) for stream in streams]
    
    if form.validate_on_submit():
        current_term = Term.query.filter_by(current=True).first()
        current_year = datetime.now().year
        school = School.query.get(current_user.school_id)
        student_id = generate_custom_student_id(school.name, current_user.school_id)

        student = Student(
            student_id=student_id,
            full_name=form.full_name.data,
            dob=form.dob.data,
            gender=form.gender.data,
            guardian_name=form.guardian_name.data,
            contact_number1=form.contact_number1.data,
            contact_number2=form.contact_number2.data,
            grade_id=form.grade.data,
            stream_id=form.stream.data,
            school_id=current_user.school_id,
            year=current_year,
            current_term_id=current_term.id,
            active=True
        )
        db.session.add(student)
        db.session.commit()
        flash('Student successfully registered!', 'success')
        return redirect(url_for('students.students'))
    else:
        flash('Form validation failed! Please check the entered data.', 'danger')

    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    terms = Term.query.all()
    all_streams = Stream.query.filter(Stream.grade_id.in_([grade.id for grade in grades])).all()

    return render_template('students/add_student.html', form=form, grades=grades, streams=all_streams, terms=terms)

@students_bp.route('/students/<string:student_id>/update', methods=['GET', 'POST'], strict_slashes=False)
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
        return redirect(url_for('students.students'))
    elif request.method == 'GET':
        print("Debugging: GET request to update student")
        form.full_name.data = student.full_name
        if student.dob:
            form.dob.data = datetime.strptime(student.dob, '%Y-%m-%d')
        form.gender.data = student.gender
        form.guardian_name.data = student.guardian_name 
        form.grade.data = student.grade 
    return render_template('students/update_student.html', form=form, student=student)

@students_bp.route('/students/<string:student_id>/inactive', methods=['POST'], strict_slashes=False)
@login_required
def toggle_student_status(student_id):
    student = Student.query.get_or_404(student_id)
    student.active = not student.active
    student.left_date = datetime.today() if not student.active else None
    db.session.commit()
    status = 'active' if student.active else 'inactive'
    flash(f'Student marked as {status}!', 'success')
    return redirect(url_for('students.students'))


@students_bp.route('/delete_student', methods=['POST'], strict_slashes=False)
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student successfully deleted!', 'success')
    return redirect(url_for('students.students'))

@students_bp.route('/search_student')
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