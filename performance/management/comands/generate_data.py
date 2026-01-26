import random
from django.core.management.base import BaseCommand
from performance.models import Student, Department, AcademicRecord

class Command(BaseCommand):
    help = 'Generates 150 random students and 2023/2024 academic records'

    def handle(self, *args, **kwargs):
        DEPARTMENTS = list(Department.objects.all())
        if not DEPARTMENTS:
            self.stdout.write(self.style.ERROR("No departments found. Create them first!"))
            return

        YEAR = "2023/2024"
        SEMESTERS = [1, 2]
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
            f_name = random.choice(first_names)
            l_name = random.choice(last_names)
            s_id = f"2023-{1000 + i}"

            student, _ = Student.objects.get_or_create(
                student_id=s_id,
                defaults={'first_name': f_name, 'last_name': l_name, 'department': dept}
            )

            for sem in SEMESTERS:
                dept_courses = COURSES.get(dept.code, ['GEN101', 'GEN102'])
                for c_code in dept_courses:
                    perf_bias = random.uniform(0.6, 1.0)
                    ca = round(random.uniform(15, 30) * perf_bias, 1)
                    mid = round(random.uniform(10, 30) * perf_bias, 1)
                    
                    # 10% chance of 0 to test "At Risk" logic
                    final = round(random.uniform(15, 40) * perf_bias, 1) if random.random() > 0.1 else 0.0

                    AcademicRecord.objects.create(
                        student=student,
                        course_code=c_code,
                        ca_total=ca,
                        mid_term=mid,
                        final_exam=final,
                        attendance_rate=round(random.uniform(0.7, 1.0), 2),
                        academic_year=YEAR,
                        semester=sem,
                        teacher_id=f"T_{random.randint(1, 10)}"
                    )

        self.stdout.write(self.style.SUCCESS(f"Successfully generated data. Total records: {AcademicRecord.objects.count()}"))