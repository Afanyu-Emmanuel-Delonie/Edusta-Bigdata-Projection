import csv
import random

# Settings
DEPARTMENTS = [
    ('SWE', 'Software Engineering'),
    ('NET', 'Networking'),
    ('ISM', 'Information Management'),
    ('ACCT', 'Accounting'),
    ('HRM', 'HR Management')
]
YEAR = '2025-2026'
TOTAL_RECORDS = 350
START_ID = 26000
FIRST_NAMES = ['Jean', 'Marie', 'Eric', 'Alice', 'Moses', 'Hope', 'Chantal', 'Kevin', 'Diane', 'Bosco', 'Aline', 'Patrick', 'Fiona', 'Justin', 'Sonia']
LAST_NAMES = ['Kamanzi', 'Umutoni', 'Gakuru', 'Mugisha', 'Uwase', 'Iradukunda', 'Keza', 'Habimana', 'Nshuti', 'Gasana']

with open('competitive_students_2026.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['registration_number', 'first_name', 'last_name', 'department_code', 'academic_year', 'ca_total', 'mid_term', 'attendance_rate'])
    
    for i in range(TOTAL_RECORDS):
        student_id = START_ID + i
        dept_code, _ = random.choice(DEPARTMENTS)
        f_name = random.choice(FIRST_NAMES)
        l_name = random.choice(LAST_NAMES)
        
        # Performance Logic for "Competition"
        if dept_code in ['SWE', 'ACCT']:
            # High Tier: Aiming for 80-95% projection
            ca = round(random.uniform(32.0, 39.5), 1)
            mid = round(random.uniform(16.0, 19.8), 1)
            attendance = round(random.uniform(92.0, 100.0), 1)
            
        elif dept_code in ['NET', 'HRM']:
            # Mid Tier: Aiming for 65-80% projection
            ca = round(random.uniform(24.0, 31.0), 1)
            mid = round(random.uniform(12.0, 16.0), 1)
            attendance = round(random.uniform(75.0, 91.0), 1)
            
        else:  # ISM
            # Low Tier: Aiming for 30-60% projection (Risk Testing)
            ca = round(random.uniform(10.0, 22.0), 1)
            mid = round(random.uniform(5.0, 11.0), 1)
            attendance = round(random.uniform(45.0, 75.0), 1)
        
        writer.writerow([student_id, f_name, l_name, dept_code, YEAR, ca, mid, attendance])

print(f"Successfully generated 350 competitive records in 'competitive_students_2026.csv'")