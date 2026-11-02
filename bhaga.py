



'''
students [0] = ID
students [1] = Name
students [2] = Course
Students [3] = Age
'''
students = [["101",'Rahul','ENGG',29],
            ["102",'Bhagya','MCA',25],
            ['103','Sonya','MCA',25],
            ['104','Bhola','ENGG',29],
            ['105','Mahajan','ENGG',70]]


def add_student():
    student_id = input("Enter Student ID: ")
    name = input("Enter Student Name: ")
    course = input("Enter Student Course: ")
    age = input("Enter Student Age: ")
    students.append([student_id, name, course, age])
    print("Student added successfully!")


def view_students():
    if not students:
        print("No students found.")
        return
    for student in students:
        print(f"ID: {student[0]}, Name: {student[1]}, Course: {student[2]}, Age: {student[3]}")


def Search_Student_by_ID(_Id):
    student = [student for student in students if student[0] == _Id]
    if student:
        print(f"ID: {student[0][0]}, Name: {student[0][1]}, Course: {student[0][2]}, Age: {student[0][3]}")
    else:
        print("No students found.")



def Search_Student_by_Name(Nmae):
    student = [student for student in students if student[1] == Nmae]
    if student:
        print(f" -> ID: {student[0][0]}, Name: {student[0][1]}, Course: {student[0][2]}, Age: {student[0][3]}")
    else:
        print("No students found.")

def Update_Student_Course(_ID):
    for i in range(len(students)):
        if students[i][0] == _ID:
            print(" -> Record Found" , students[i][1])
            students[i][2] = input(f"Update course for {students[i][1]}  ->  ")



def Delete_Student_(_ID):
    for i in range(0,len(students)):
        if students[i][0] == _ID:
            #if pop is done the list size will modify so loop should not go beyond break is needed
            print(" -> Record Deleted " , students[i][1])
            students.pop(i)
            break


input_choice = None

while input_choice != 8:
    
    print(
'''
   ---------------------------
   | 1. Add Student           |
   ---------------------------
   | 2. View All Students     |
   ---------------------------
   | 3. Search Student by ID  |
   ---------------------------
   | 4. Search Student by Name|
   ---------------------------
   | 5. Update Student Course |
   ---------------------------
   | 6. Delete Student        |
   ---------------------------
   | 7. Count Students        |
   ---------------------------
   | 8. Exit                  |
   --------------------------''')
    input_choice = int(input("Enter your choice (1-8): "))

    if input_choice == 1:
        #ADD STUDENT
        student_id = input("Enter Student ID: ")
        name = input("Enter Student Name: ")
        course = input("Enter Student Course: ")
        age = input("Enter Student Age: ")
        students.append([student_id, name, course, age])
        print("Student added successfully!")

    elif input_choice == 2:
        view_students()

    elif input_choice == 3:
        student_id = input("Enter Student ID to search:  -> ")
        Search_Student_by_ID(student_id)

    elif input_choice == 4:
        Student_name = input("Enter Student Name to search:  -> ")
        Search_Student_by_Name(Student_name)

    elif input_choice == 5:
        Student_name = input("Enter Student ID to search:  -> ")
        Update_Student_Course(Student_name)

    elif input_choice == 6:
        Student_name = input("Enter Student ID to search:  -> ")
        Delete_Student_(Student_name)

    elif input_choice == 7:
        print(f"\n  -> Total no of records {len(students)}"  )

    elif input_choice == 8:
        print("Exiting the program.")
        break