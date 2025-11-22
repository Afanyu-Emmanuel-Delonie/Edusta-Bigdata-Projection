"""
CSV/Excel Upload Processor
Handles file uploads, validation, and data import using Pandas
"""

import pandas as pd
import numpy as np
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Student, Course, Semester, Group, Performance, 
    UploadHistory
)

class CSVProcessor:
    """
    Processes CSV/Excel files and imports student performance data
    """
    
    # Required columns in CSV
    REQUIRED_COLUMNS = [
        'Student_ID', 'First_Name', 'Last_Name', 'Department',
        'Course', 'Group', 'Semester', 'Score'
    ]
    
    # Optional columns
    OPTIONAL_COLUMNS = ['Grade', 'Performance_Status', 'Ranking']
    
    def __init__(self, file_path, user):
        """
        Initialize processor with file path and user
        
        Args:
            file_path: path to uploaded CSV/Excel file
            user: Django User object who uploaded the file
        """
        self.file_path = file_path
        self.user = user
        self.df = None
        self.errors = []
        self.success_count = 0
        self.error_count = 0
    
    def read_file(self):
        """
        Read CSV or Excel file into Pandas DataFrame
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_extension = self.file_path.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                self.df = pd.read_csv(self.file_path)
            elif file_extension in ['xlsx', 'xls']:
                self.df = pd.read_excel(self.file_path)
            else:
                self.errors.append(f"Unsupported file format: {file_extension}")
                return False
            
            # Strip whitespace from column names
            self.df.columns = self.df.columns.str.strip()
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return False
    
    def validate_columns(self):
        """
        Validate that all required columns are present
        
        Returns:
            bool: True if valid, False otherwise
        """
        missing_columns = []
        
        for col in self.REQUIRED_COLUMNS:
            if col not in self.df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            self.errors.append(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
            return False
        
        return True
    
    def clean_data(self):
        """
        Clean and prepare data for import
        """
        # Remove rows with missing Student_ID
        original_count = len(self.df)
        self.df = self.df.dropna(subset=['Student_ID'])
        
        if len(self.df) < original_count:
            removed = original_count - len(self.df)
            self.errors.append(f"Removed {removed} rows with missing Student_ID")
        
        # Convert Student_ID to string and ensure 5 digits
        self.df['Student_ID'] = self.df['Student_ID'].astype(str).str.zfill(5)
        
        # Clean string columns
        string_columns = ['First_Name', 'Last_Name', 'Department', 'Course', 'Group', 'Semester']
        for col in string_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        
        # Convert Score to float
        self.df['Score'] = pd.to_numeric(self.df['Score'], errors='coerce')
        
        # Remove rows with invalid scores
        invalid_scores = self.df['Score'].isna() | (self.df['Score'] < 0) | (self.df['Score'] > 100)
        if invalid_scores.any():
            count = invalid_scores.sum()
            self.errors.append(f"Removed {count} rows with invalid scores")
            self.df = self.df[~invalid_scores]
    
    def get_or_create_student(self, row):
        """
        Get or create student from row data
        
        Args:
            row: pandas Series with student data
        
        Returns:
            Student object or None
        """
        try:
            student_id = row['Student_ID']
            
            student, created = Student.objects.get_or_create(
                student_id=student_id,
                defaults={
                    'first_name': row['First_Name'],
                    'last_name': row['Last_Name'],
                    'email': f"{student_id}@auca.ac.rw",
                    'department': row['Department'],
                }
            )
            
            # Update existing student info if needed
            if not created:
                student.first_name = row['First_Name']
                student.last_name = row['Last_Name']
                student.department = row['Department']
                student.save()
            
            return student
        
        except Exception as e:
            self.errors.append(f"Error creating student {row['Student_ID']}: {str(e)}")
            return None
    
    def get_or_create_course(self, course_code, department):
        """
        Get or create course
        
        Args:
            course_code: course code string
            department: department string
        
        Returns:
            Course object or None
        """
        try:
            course, created = Course.objects.get_or_create(
                code=course_code,
                defaults={
                    'name': course_code,  # Use code as name if not found
                    'department': department,
                    'teacher': self.user if hasattr(self.user, 'role') else None,
                }
            )
            
            return course
        
        except Exception as e:
            self.errors.append(f"Error creating course {course_code}: {str(e)}")
            return None
    
    def get_or_create_semester(self, semester_name):
        """
        Get or create semester
        
        Args:
            semester_name: semester name (e.g., "Fall 2024")
        
        Returns:
            Semester object or None
        """
        try:
            # Try to parse semester name
            parts = semester_name.split()
            if len(parts) >= 2:
                semester_type = parts[0]
                year = int(parts[1])
            else:
                semester_type = "Fall"
                year = 2024
            
            semester, created = Semester.objects.get_or_create(
                name=semester_name,
                defaults={
                    'semester_type': semester_type,
                    'year': year,
                    'start_date': f"{year}-01-01",
                    'end_date': f"{year}-12-31",
                }
            )
            
            return semester
        
        except Exception as e:
            self.errors.append(f"Error creating semester {semester_name}: {str(e)}")
            return None
    
    def get_or_create_group(self, group_name, course, semester):
        """
        Get or create group
        
        Args:
            group_name: group name string
            course: Course object
            semester: Semester object
        
        Returns:
            Group object or None
        """
        try:
            group, created = Group.objects.get_or_create(
                name=group_name,
                course=course,
                semester=semester,
                defaults={
                    'max_students': 30,
                }
            )
            
            return group
        
        except Exception as e:
            self.errors.append(f"Error creating group {group_name}: {str(e)}")
            return None
    
    def process_row(self, row):
        """
        Process a single row and create Performance record
        
        Args:
            row: pandas Series with performance data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get or create related objects
            student = self.get_or_create_student(row)
            if not student:
                return False
            
            course = self.get_or_create_course(row['Course'], row['Department'])
            if not course:
                return False
            
            semester = self.get_or_create_semester(row['Semester'])
            if not semester:
                return False
            
            group = self.get_or_create_group(row['Group'], course, semester)
            if not group:
                return False
            
            # Create or update Performance record
            performance, created = Performance.objects.update_or_create(
                student=student,
                course=course,
                semester=semester,
                defaults={
                    'group': group,
                    'score': Decimal(str(row['Score'])),
                    'uploaded_by': self.user,
                }
            )
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error processing row for student {row.get('Student_ID', 'Unknown')}: {str(e)}")
            return False
    
    def process(self):
        """
        Main processing function
        Reads file, validates, cleans, and imports data
        
        Returns:
            dict with results: success_count, error_count, errors
        """
        # Step 1: Read file
        if not self.read_file():
            return {
                'success': False,
                'success_count': 0,
                'error_count': 0,
                'errors': self.errors,
            }
        
        # Step 2: Validate columns
        if not self.validate_columns():
            return {
                'success': False,
                'success_count': 0,
                'error_count': 0,
                'errors': self.errors,
            }
        
        # Step 3: Clean data
        self.clean_data()
        
        # Step 4: Process each row
        total_rows = len(self.df)
        
        for index, row in self.df.iterrows():
            if self.process_row(row):
                self.success_count += 1
            else:
                self.error_count += 1
        
        # Step 5: Save upload history
        self.save_upload_history()
        
        return {
            'success': True,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'total_rows': total_rows,
            'errors': self.errors,
        }
    
    def save_upload_history(self):
        """
        Save upload history to database
        """
        try:
            UploadHistory.objects.create(
                uploaded_by=self.user,
                file_name=self.file_path.name,
                file_path=self.file_path,
                records_count=self.success_count + self.error_count,
                success_count=self.success_count,
                error_count=self.error_count,
                errors_log='\n'.join(self.errors) if self.errors else '',
            )
        except Exception as e:
            print(f"Error saving upload history: {str(e)}")


def process_csv_upload(file, user):
    """
    Convenience function to process CSV upload
    
    Args:
        file: uploaded file object
        user: Django User object
    
    Returns:
        dict with processing results
    """
    processor = CSVProcessor(file, user)
    results = processor.process()
    
    # After successful import, calculate rankings
    if results['success'] and results['success_count'] > 0:
        from .analysis import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer(user)
        analyzer.calculate_rankings()
        analyzer.generate_recommendations()
    
    return results