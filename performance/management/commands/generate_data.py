import random
from django.core.management.base import BaseCommand
from performance.models import Student, Department, AcademicRecord


class Command(BaseCommand):
    help = 'Generates 150 random students and academic records for testing'

    def handle(self, *args, **kwargs):
        DEPARTMENTS = list(Department.objects.all())
        if not DEPARTMENTS:
            self.stdout.write(self.style.ERROR("No departments found. Create them first!"))
            return

        YEAR = "2023/2024"
        COURSES = {
            'IT': ['IT101', 'NET202', 'DB303', 'SEC404'],
            'SE': ['SOFT101', 'JAVA202', 'ARCH303', 'TEST404'],
            'CS': ['ALGO101', 'OS202', 'COMP303', 'AI404'],
            'MGMT': ['BUS101', 'HR202', 'ECON303'],
        }
        first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

        self.stdout.write("Generating 150 students...")

        for i in range(150):
            dept = random.choice(DEPARTMENTS)
            student, _ = Student.objects.get_or_create(
                student_id=f"2023-{1000 + i}",
                defaults={
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'department': dept,
                    'current_gpa': 0,
                }
            )
            dept_courses = COURSES.get(dept.code, ['GEN101', 'GEN102'])
            for c_code in dept_courses:
                bias = random.uniform(0.6, 1.0)
                AcademicRecord.objects.create(
                    student=student,
                    course_code=c_code,
                    ca_total=round(random.uniform(15, 30) * bias, 1),
                    mid_term=round(random.uniform(10, 30) * bias, 1),
                    final_exam=round(random.uniform(15, 40) * bias, 1) if random.random() > 0.1 else 0.0,
                    attendance_rate=round(random.uniform(0.7, 1.0), 2),
                    academic_year=YEAR,
                    teacher_id=f"T_{random.randint(1, 10)}",
                )

        self.stdout.write(self.style.SUCCESS(
            f"Done. Total records: {AcademicRecord.objects.count()}"
        ))
