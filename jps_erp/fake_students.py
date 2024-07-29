from jps_erp import app, db
from jps_erp.models import Student
from jps_erp.utils import generate_custom_student_id
from datetime import datetime
import random

# Function to generate random student names
def generate_student_name():
    first_names = ["John", "Jane", "Alex", "Emily", "Chris", "Katie", "Mike", "Laura"]
    last_names = ["Gallagher", "Nyambura", "Johnson", "Jones", "Karanja", "Davis", "Miller", "Wilson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Function to generate a random date of birth
def generate_dob():
    start_date = datetime.strptime('2010-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2015-12-31', '%Y-%m-%d')
    return start_date + (end_date - start_date) * random.random()

# Function to generate a random grade
def generate_grade():
    return random.choice(["Playgroup", "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"])

with app.app_context():
    students = []
    for i in range(100):
        student = Student(
            student_id=generate_custom_student_id,
            full_name=generate_student_name(),
            dob=generate_dob(),
            gender=random.choice(["Male", "Female"]),
            guardian_name=generate_student_name(),
            contact_number1=f"0712{random.randint(100000, 999999)}",
            contact_number2=f"0722{random.randint(100000, 999999)}",
            grade=f"Grade {(i // 25) + 1}",  # Distribute 25 students for each grade (1-4)
            school_id=1,  # Kiganjo Jnr School
            year=2024,
            current_term_id=1,  # Term 2 of 2024
            active=True
        )
        students.append(student)
        print(f"Debugging: Added student {student.full_name}")

    # Add all students to the session
    db.session.add_all(students)

    # Commit the session to save students to the database
    db.session.commit()
    print("Debugging: Committed all students to the database")

