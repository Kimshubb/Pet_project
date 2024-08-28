import random
from faker import Faker
from datetime import datetime
from jps_erp import db
from jps_erp.models import Student, School, Term, Grade, Stream
from jps_erp.utils import generate_custom_student_id  # Ensure this import is correct

def populate_school_with_students(school_id, num_students=1000):
    faker = Faker()

    # Retrieve the school and current term
    school = School.query.get(school_id)
    if not school:
        print(f"School with ID {school_id} not found.")
        return
    
    current_term = Term.query.filter_by(current=True).first()
    current_year = datetime.now().year
    grades = Grade.query.filter_by(school_id=school_id).all()

    if not grades:
        print(f"No grades found for school with ID {school_id}.")
        return
    
    for grade in grades:
        # Ensure there are at least 2 streams for each grade
        streams = Stream.query.filter_by(grade_id=grade.id).all()
        if len(streams) < 2:
            existing_stream_names = [stream.name for stream in streams]
            for i in range(2 - len(streams)):
                stream_name = f"Stream {chr(65 + i)}"  # Example: "Stream A", "Stream B"
                if stream_name not in existing_stream_names:
                    stream = Stream(name=stream_name, grade_id=grade.id)
                    db.session.add(stream)
                    existing_stream_names.append(stream_name)
            db.session.commit()
            streams = Stream.query.filter_by(grade_id=grade.id).all()  # Refresh streams

        for _ in range(num_students // len(grades)):
            # Randomly select a stream from the grade
            stream = random.choice(streams)

            # Generate random student data with length constraints
            full_name = faker.name()[:20]  # Full name with a max length of 100 characters
            dob = faker.date_of_birth(minimum_age=5, maximum_age=18)  # Date of birth within a reasonable range
            gender = random.choice(['Male', 'Female'])  # Gender limited to 'Male' or 'Female'
            guardian_name = faker.name()[:20]  # Guardian name with a max length of 100 characters
            contact_number1 = faker.phone_number()[:12]  # Primary contact number with a max length of 20 characters
            contact_number2 = faker.phone_number()[:12]  # Secondary contact number with a max length of 20 characters
            cf_balance = round(random.uniform(0, 1000), 2)  # Random float for balance, rounded to 2 decimal places

            # Generate a student ID that fits within 10 characters
            student_id = generate_custom_student_id(school.name, school_id)

            # Create the student record
            student = Student(
                student_id=student_id,
                full_name=full_name,
                dob=dob,
                gender=gender,
                guardian_name=guardian_name,
                contact_number1=contact_number1,
                contact_number2=contact_number2,
                grade_id=grade.id,
                stream_id=stream.id,
                school_id=school_id,
                year=current_year,
                current_term_id=current_term.id if current_term else None,
                cf_balance=cf_balance,
                active=True
            )

            # Add the student to the session
            db.session.add(student)
    
    # Commit the session to save all students to the database
    db.session.commit()
    print(f"Successfully added {num_students} students to school ID {school_id}.")
