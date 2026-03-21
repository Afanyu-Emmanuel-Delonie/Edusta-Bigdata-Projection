"""
Standalone script to generate sample student CSV data for testing.
Run from project root: python scripts/generate_data.py
"""

import csv
import random

DEPARTMENTS = [
    ('SWE', 'Software Engineering'),
    ('NET', 'Networking'),
    ('ISM', 'Information Management'),
    ('ACCT', 'Accounting'),
    ('HRM', 'HR Management'),
]
YEAR = '2025/2026'
TOTAL_RECORDS = 350
START_ID = 26000
FIRST_NAMES = ['Jean', 'Marie', 'Eric', 'Alice', 'Moses', 'Hope', 'Chantal', 'Kevin', 'Diane', 'Bosco', 'Aline', 'Patrick', 'Fiona', 'Justin', 'Sonia']
LAST_NAMES = ['Kamanzi', 'Umutoni', 'Gakuru', 'Mugisha', 'Uwase', 'Iradukunda', 'Keza', 'Habimana', 'Nshuti', 'Gasana']

with open('sample_students.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['student_id', 'first_name', 'last_name', 'department_code', 'academic_year', 'ca_total', 'mid_term', 'attendance_rate'])

    for i in range(TOTAL_RECORDS):
        dept_code, _ = random.choice(DEPARTMENTS)
        if dept_code in ['SWE', 'ACCT']:
            ca = round(random.uniform(32.0, 39.5), 1)
            mid = round(random.uniform(16.0, 19.8), 1)
            attendance = round(random.uniform(92.0, 100.0), 1)
        elif dept_code in ['NET', 'HRM']:
            ca = round(random.uniform(24.0, 31.0), 1)
            mid = round(random.uniform(12.0, 16.0), 1)
            attendance = round(random.uniform(75.0, 91.0), 1)
        else:
            ca = round(random.uniform(10.0, 22.0), 1)
            mid = round(random.uniform(5.0, 11.0), 1)
            attendance = round(random.uniform(45.0, 75.0), 1)

        writer.writerow([
            START_ID + i,
            random.choice(FIRST_NAMES),
            random.choice(LAST_NAMES),
            dept_code,
            YEAR,
            ca,
            mid,
            attendance,
        ])

print(f"Generated {TOTAL_RECORDS} records → sample_students.csv")
