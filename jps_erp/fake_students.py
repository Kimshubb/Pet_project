with app.app_context():
    students = []
    for i in range(100):
        student = Student(
            student_id=generate_custom_student_id('Junior Precious School', 1),
            full_name=generate_student_name(),
            dob=generate_dob(),
            gender=random.choice(["Male", "Female"]),
            guardian_name=generate_student_name(),
            contact_number1=f"0712{random.randint(100000, 999999)}",
            contact_number2=f"0722{random.randint(100000, 999999)}",
            grade=f"Grade {(i // 25) + 1}",  # Distribute 25 students for each grade (1-4)
            school_id=7,  # Kiganjo Jnr School
            year=2024,
            current_term_id=10,  # Term 2 of 2024
            active=True
        )
        students.append(student)
        print(f"Debugging: Added student {student.full_name}")
    db.session.add_all(students)
    db.session.commit()
    print("Debugging: All students added successfully")
