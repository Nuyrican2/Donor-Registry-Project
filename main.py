class Student:
    def __init__(self, name, gpa, sat_score, essays):
        self.name = name
        self.gpa = gpa
        self.sat_score = sat_score
        self.essays = essays
        self.status = "Pending"
    
    def __repr__(self):
        return f"Student({self.name}, GPA: {self.gpa}, SAT: {self.sat_score})"


class CollegeAdmissions:
    def __init__(self):
        self.applications = []
    
    def submit_application(self, student):
        self.applications.append(student)
        print(f"Application submitted for {student.name}")
    
    def evaluate_application(self, student):
        # Simple evaluation criteria
        if student.gpa >= 3.8 and student.sat_score >= 1500:
            student.status = "Accepted"
        elif student.gpa >= 3.5 and student.sat_score >= 1400:
            student.status = "Reviewed"
        else:
            student.status = "Rejected"
        return student.status
    
    def get_applications_by_status(self, status):
        return [s for s in self.applications if s.status == status]
    
    def display_all_applications(self):
        for student in self.applications:
            print(f"{student.name} - {student.status}")


# Example usage
if __name__ == "__main__":
    admissions = CollegeAdmissions()
    
    student1 = Student("Alice", 3.9, 1550, "Strong essays")
    student2 = Student("Bob", 3.6, 1420, "Good essays")
    student3 = Student("Charlie", 3.2, 1300, "Average essays")
    
    for student in [student1, student2, student3]:
        admissions.submit_application(student)
        admissions.evaluate_application(student)
    
    admissions.display_all_applications()