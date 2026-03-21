"""
Data Import Service
Handles bulk CSV/Excel uploads with transactional integrity.
"""

import pandas as pd
from django.db import transaction
from ..models import Student, AcademicRecord, Department

TARGET_YEAR = "2025/2026"


def import_records_from_file(file, academic_year=TARGET_YEAR):
    """
    Parse and import student records from a CSV or Excel file.

    Returns:
        (success: bool, message: str, count: int)
    """
    try:
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)

        with transaction.atomic():
            for _, row in df.iterrows():
                student_id = row.get('student_id') or row.get('registration_number')

                dept, _ = Department.objects.get_or_create(
                    code=row['department_code'],
                    defaults={'name': row.get('department_name', row['department_code'])}
                )

                student, _ = Student.objects.get_or_create(
                    student_id=student_id,
                    defaults={
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'department': dept,
                        'current_gpa': row.get('ca_total', 0) / 10,
                    }
                )

                AcademicRecord.objects.create(
                    student=student,
                    course_code=row.get('course_code', 'GEN101'),
                    academic_year=row.get('academic_year', academic_year),
                    ca_total=row.get('ca_total', 0),
                    mid_term=row.get('mid_term', 0),
                    final_exam=row.get('final_exam', 0),
                    attendance_rate=row.get('attendance_rate', row.get('attendance', 0)),
                    teacher_id=row.get('teacher_id', 'T001'),
                )

        return True, f'Successfully imported {len(df)} records', len(df)

    except Exception as e:
        return False, str(e), 0
