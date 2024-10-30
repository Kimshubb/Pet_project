from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from jps_erp.models import Grade, Stream, Subject, User, TeacherProfile, TimeTable, teacher_subject
from jps_erp import db
from . import schedules_bp
import random
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from jps_erp.decoraters import admin_required

LESSON_REQUIREMENTS = {
    "lower_primary": {
        "Indigenous Language Activities": 1,
        "Kiswahili Language Activities": 4,
        "English Language Activities": 5,
        "Mathematical Activities": 5,
        "Religious Education Activities": 3,
        "Environmental Activities": 4,
        "Creative Activities": 7,
        "Pastoral/Religious Instruction Programme": 1
    },
    "upper_primary": {
        # Define subjects and their lesson requirements for upper primary
    },
    "junior": {
        # Define subjects and their lesson requirements for junior level
    }
}

def get_education_levels_from_db():
    """
    Dynamically query the database to classify grades into education levels.
    Returns a dictionary with keys as education levels and values as lists of grade names.
    """
    grades = Grade.query.filter_by(school_id=current_user.school_id).all()
    education_levels = {
        'lower_primary': [],
        'upper_primary': [],
        'junior': []
    }

    # Classify grades based on their names or other criteria
    for grade in grades:
        if 'Grade 1' <= grade.name <= 'Grade 3':
            education_levels['lower_primary'].append(grade.name)
        elif 'Grade 4' <= grade.name <= 'Grade 6':
            education_levels['upper_primary'].append(grade.name)
        elif 'Grade 7' <= grade.name <= 'Grade 8':
            education_levels['junior'].append(grade.name)

    return education_levels

@schedules_bp.route('/schedules', methods=['GET'])
@login_required
def schedules():
    return render_template('schedules/schedules.html')

@schedules_bp.route('/get_education_levels', methods=['GET'])
@login_required
def get_education_levels():
    education_levels = get_education_levels_from_db()
    return jsonify(list(education_levels.keys()))

@schedules_bp.route('/get_teachers/<education_level>', methods=['GET'])
@login_required
def get_teachers(education_level):
    education_levels = get_education_levels_from_db()
    if education_level not in education_levels:
        return jsonify({'error': 'Invalid education level'}), 400

    grades = education_levels[education_level]
    teachers = (
        User.query
        .join(TeacherProfile)
        .filter(
            User.school_id == current_user.school_id,
            User.role == 'teacher'
        )
        .distinct()
        .all()
    )

    return jsonify([
        {'id': str(teacher.id), 'name': teacher.username}
        for teacher in teachers
    ])



@schedules_bp.route('/get_subjects/<education_level>', methods=['GET'])
@login_required
def get_subjects(education_level):
    education_levels = get_education_levels_from_db()
    if education_level not in education_levels:
        return jsonify({'error': 'Invalid education level'}), 400

    grades = education_levels[education_level]
    subjects = (
        Subject.query
        .join(Grade)
        .filter(
            Grade.name.in_(grades),
            Grade.school_id == current_user.school_id
        )
        .distinct()
        .all()
    )

    return jsonify({
        str(subject.id): subject.name
        for subject in subjects
    })

@schedules_bp.route('/assign_teachers', methods=['POST'])
@login_required
def assign_teachers():
    data = request.json
    education_level = data.get('education_level')
    teacher_ids = data.get('teacher_ids', [])

    if education_level not in education_levels:
        return jsonify({'error': 'Invalid education level'}), 400

    grades = education_levels[education_level]
    
    try:
        for teacher_id in teacher_ids:
            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != 'teacher':
                return jsonify({'error': f'Invalid teacher ID: {teacher_id}'}), 400

            # Ensure the teacher has a TeacherProfile
            if not teacher.teacher_profile:
                teacher_profile = TeacherProfile(user_id=teacher.id, school_id=teacher.school_id)
                db.session.add(teacher_profile)

            # Assign teacher to all grades in the education level
            for grade_name in grades:
                grade = Grade.query.filter_by(name=grade_name, school_id=current_user.school_id).first()
                if grade:
                    for subject in grade.subjects:
                        if subject not in teacher.teacher_profile.subjects:
                            teacher.teacher_profile.subjects.append(subject)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Teachers assigned successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Error assigning teachers. Please try again.'}), 500

@schedules_bp.route('/assign_subjects', methods=['POST'])
@login_required
def assign_subjects():
    data = request.json
    teacher_subject_assignments = data.get('assignments', [])

    try:
        for assignment in teacher_subject_assignments:
            teacher_id = assignment['teacher_id']
            subject_ids = assignment['subject_ids']

            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != 'teacher':
                return jsonify({'error': f'Invalid teacher ID: {teacher_id}'}), 400

            # Clear existing subject assignments for this teacher
            teacher.teacher_profile.subjects = []

            # Assign new subjects
            for subject_id in subject_ids:
                subject = Subject.query.get(subject_id)
                if subject:
                    teacher.teacher_profile.subjects.append(subject)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Subjects assigned successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Error assigning subjects. Please try again.'}), 500

@schedules_bp.route('/generate_timetable', methods=['POST'])
@login_required
def generate_timetable():
    data = request.json
    education_level = data.get('education_level')
    start_time = datetime.strptime(data.get('start_time', '08:00'), '%H:%M').time()

    if education_level not in education_levels:
        return jsonify({'error': 'Invalid education level'}), 400

    grades = education_levels[education_level]

    try:
        for grade_name in grades:
            grade = Grade.query.filter_by(name=grade_name, school_id=current_user.school_id).first()
            if grade:
                for stream in grade.streams:
                    generate_stream_timetable(grade, stream, start_time)

        return jsonify({'success': True, 'message': f'Timetables generated successfully for {education_level}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error generating timetables: {str(e)}'}), 500

def generate_stream_timetable(grade, stream, start_time):
    # Delete existing timetable entries for this stream
    TimeTable.query.filter_by(stream_id=stream.id).delete()

    subjects = Subject.query.filter_by(grade_id=grade.id).all()
    teachers = User.query.join(TeacherProfile).join(teacher_subject).filter(
        teacher_subject.c.subject_id.in_([s.id for s in subjects])
    ).all()

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    lesson_duration = timedelta(minutes=40)
    break_duration = timedelta(minutes=10)
    lunch_duration = timedelta(minutes=60)

    for day in days_of_week:
        current_time = start_time

        for lesson_num in range(1, 9):  # 8 lessons per day
            if lesson_num == 4:  # Short break after 3rd lesson
                current_time = (datetime.combine(datetime.today(), current_time) + break_duration).time()
            elif lesson_num == 6:  # Lunch break after 5th lesson
                current_time = (datetime.combine(datetime.today(), current_time) + lunch_duration).time()

            subject = random.choice(subjects)
            teacher = random.choice([t for t in teachers if subject in t.teacher_profile.subjects])

            end_time = (datetime.combine(datetime.today(), current_time) + lesson_duration).time()

            timetable_entry = TimeTable(
                day_of_week=day,
                start_time=current_time,
                end_time=end_time,
                teacher_id=teacher.teacher_profile.id,
                subject_id=subject.id,
                stream_id=stream.id,
                school_id=current_user.school_id
            )
            db.session.add(timetable_entry)

            current_time = end_time

    db.session.commit()

@schedules_bp.route('/get_timetable/<int:stream_id>', methods=['GET'])
@login_required
def get_timetable(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    
    if stream.grade.school_id != current_user.school_id:
        return jsonify({'error': 'Unauthorized'}), 403

    timetable_entries = (
        TimeTable.query
        .filter_by(stream_id=stream_id)
        .order_by(TimeTable.day_of_week, TimeTable.start_time)
        .all()
    )

    timetable_data = {}
    for entry in timetable_entries:
        day = entry.day_of_week
        if day not in timetable_data:
            timetable_data[day] = []
        
        timetable_data[day].append({
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'subject': entry.subject.name,
            'teacher': entry.teacher.user.username
        })

    return jsonify(timetable_data)

@schedules_bp.route('/get_all_teachers', methods=['GET'])
@login_required
def get_all_teachers():
    teachers = (
        User.query
        .filter(
            User.school_id == current_user.school_id,
            User.role == 'teacher'
        )
        .all()
    )
    return jsonify([
        {'id': str(teacher.id), 'name': teacher.username}
        for teacher in teachers
    ])

@schedules_bp.route('/assign_lesson', methods=['POST'])
@login_required
@admin_required
def assign_lesson():
    data = request.json
    grade_id = data.get('grade_id')
    stream_id = data.get('stream_id')
    teacher_id = data.get('teacher_id')
    subject_id = data.get('subject_id')

    try:
        # Validate the entities exist
        grade = Grade.query.get_or_404(grade_id)
        stream = Stream.query.get_or_404(stream_id)
        teacher = User.query.get_or_404(teacher_id)
        subject = Subject.query.get_or_404(subject_id)

        # Make sure the teacher has a TeacherProfile
        if not teacher.teacher_profile:
            return jsonify({'error': 'Teacher does not have a profile.'}), 400

        # Create or update a timetable entry for the teacher, subject, and stream
        timetable_entry = TimeTable(
            day_of_week='Monday',  # Default day, you can modify this to be dynamic
            start_time='08:00',    # Default time, can also be dynamic
            end_time='09:00',
            teacher_id=teacher.teacher_profile.id,
            subject_id=subject.id,
            stream_id=stream.id,
            school_id=current_user.school_id
        )
        db.session.add(timetable_entry)
        db.session.commit()

        return jsonify({'success': True})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Error assigning lesson. Please try again.'}), 500

"""
@schedules_bp.route('/assign_teachers_to_streams', methods=['POST'])
@login_required
def assign_teachers_to_streams():
    data = request.json
    assignments = data.get('assignments', [])  # Expecting a list of {teacher_id, grade_id, stream_id, subject_id}
    
    try:
        for assignment in assignments:
            teacher_id = assignment['teacher_id']
            grade_id = assignment['grade_id']
            stream_id = assignment['stream_id']
            subject_id = assignment['subject_id']

            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != 'teacher':
                return jsonify({'error': f'Invalid teacher ID: {teacher_id}'}), 400

            # Ensure the teacher has a TeacherProfile
            if not teacher.teacher_profile:
                teacher_profile = TeacherProfile(user_id=teacher.id, school_id=teacher.school_id)
                db.session.add(teacher_profile)

            subject = Subject.query.get(subject_id)
            stream = Stream.query.get(stream_id)

            if subject and stream:
                # Assign teacher to subject within the stream
                teacher.teacher_profile.subjects.append(subject)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Teachers assigned to subjects successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Error assigning teachers. Please try again.'}), 500
"""