"""
CSV/Excel Processing Module
Handles file uploads and data imports with override capability
"""

import pandas as pd
import io
from django.db import transaction
from .models import Student, Course, Semester, Group, Performance, Dataset


def process_csv_upload(file, user, dataset_name, dataset_description='', course=None, semester=None):
    """
    Process CSV/Excel file upload with dataset override
    
    Args:
        file: Uploaded file object
        user: User uploading the file
        dataset_name: Name for the dataset
        dataset_description: Optional description
        course: Course object (optional)
        semester: Semester object (required)
    
    Returns:
        Dictionary with success status and results
    """
    try:
        # Read file based on extension
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        else:
            return {
                'success': False,
                'errors': ['Unsupported file format. Please upload CSV or Excel file.']
            }
        
        # Print original columns for debugging
        print(f"DEBUG: Original columns: {list(df.columns)}")
        
        # Clean column names aggressively
        # 1. Strip whitespace
        # 2. Replace spaces/underscores with nothing temporarily to check content
        # 3. Convert to lowercase
        df.columns = df.columns.str.strip().str.replace('_', '').str.replace(' ', '').str.lower()
        
        print(f"DEBUG: Cleaned columns: {list(df.columns)}")
        
        # Map expected columns (all lowercase, no spaces/underscores)
        column_mapping = {
            'studentid': 'student_id',
            'firstname': 'first_name', 
            'lastname': 'last_name',
            'departmen': 'department',  # Handle the typo in your dataset
            'department': 'department',
            'course': 'course_code',
            'coursecode': 'course_code',
            'group': 'group',
            'semester': 'semester',
            'score': 'score',
            'grade': 'grade',
            'performance': 'performance_status',
            'email': 'email',
            'attendance': 'attendance',
            'ranking': 'ranking'
        }
        
        # Rename columns based on mapping
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        
        print(f"DEBUG: Final mapped columns: {list(df.columns)}")
        
        # Validate required columns (course_code is now optional)
        required_columns = ['student_id', 'first_name', 'last_name', 'score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'errors': [
                    f'Missing required columns: {", ".join(missing_columns)}.',
                    f'Original columns found: {", ".join(df.columns)}',
                    'Required: student_id, first_name, last_name, score'
                ]
            }
        
        # START TRANSACTION - Delete old data and insert new
        with transaction.atomic():
            # Step 1: Delete ALL existing performance records
            deleted_count = Performance.objects.all().count()
            Performance.objects.all().delete()
            
            # Step 2: Optionally delete old datasets (clean slate)
            Dataset.objects.all().delete()
            
            # Step 3: Create new dataset
            dataset = Dataset.objects.create(
                name=dataset_name,
                description=dataset_description,
                semester=semester,
                course=course,
                uploaded_by=user if user and user.is_authenticated else None,
                is_active=True
            )
            
            print(f"DEBUG: Processing {len(df)} rows")
            
            # Step 4: Process new data
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Debug print for first few rows
                    if index < 3:
                        print(f"DEBUG Row {index}: {dict(row)}")
                    
                    # Get or create student
                    student_id_val = str(row['student_id']).strip()
                    first_name_val = str(row['first_name']).strip()
                    last_name_val = str(row['last_name']).strip()
                    
                    # Generate email if not provided
                    if 'email' in row and pd.notna(row['email']):
                        email_val = str(row['email']).strip()
                    else:
                        email_val = f"{student_id_val}@student.edu"
                    
                    # Get department (handle the typo 'departmen' in your dataset)
                    if 'department' in row and pd.notna(row['department']):
                        department_val = str(row['department']).strip()
                    else:
                        department_val = 'General'
                    
                    student, created = Student.objects.get_or_create(
                        student_id=student_id_val,
                        defaults={
                            'first_name': first_name_val,
                            'last_name': last_name_val,
                            'email': email_val,
                            'department': department_val
                        }
                    )
                    
                    if created and index < 5:
                        print(f"DEBUG: Created student {student_id_val}")
                    
                    # Get or create course (now optional with fallback)
                    if 'course_code' in row and pd.notna(row['course_code']):
                        course_code = str(row['course_code']).strip()
                    elif course:  # Use course from upload form if provided
                        course_code = course.code
                    else:
                        course_code = 'GENERAL'  # Default fallback
                    
                    course_obj, created = Course.objects.get_or_create(
                        code=course_code,
                        defaults={
                            'name': course_code if course_code != 'GENERAL' else 'General Course',
                            'department': department_val,
                            'credits': 3
                        }
                    )
                    
                    if created and index < 5:
                        print(f"DEBUG: Created course {course_code}")
                    
                    # Use provided semester or get from CSV
                    if semester:
                        semester_obj = semester
                    else:
                        if 'semester' in row and pd.notna(row['semester']):
                            semester_name = str(row['semester']).strip()
                        else:
                            semester_name = 'Default Semester'
                        
                        semester_obj, _ = Semester.objects.get_or_create(
                            name=semester_name,
                            defaults={
                                'semester_type': 'Fall',
                                'year': 2024,
                                'start_date': '2024-01-01',
                                'end_date': '2024-05-31',
                                'is_active': True
                            }
                        )
                    
                    # Get or create group (optional)
                    group_obj = None
                    if 'group' in row and pd.notna(row['group']):
                        group_name = str(row['group']).strip()
                        group_obj, _ = Group.objects.get_or_create(
                            name=group_name,
                            course=course_obj,
                            semester=semester_obj,
                            defaults={
                                'max_students': 30
                            }
                        )
                    
                    # Parse score
                    score_val = float(row['score'])
                    
                    # Create performance record
                    perf = Performance.objects.create(
                        student=student,
                        course=course_obj,
                        semester=semester_obj,
                        group=group_obj,
                        dataset=dataset,
                        score=score_val,
                        uploaded_by=user if user and user.is_authenticated else None
                    )
                    
                    success_count += 1
                    
                    if index < 3:
                        print(f"DEBUG: Created performance {perf.id} - Student: {student_id_val}, Score: {score_val}, Grade: {perf.grade}")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: {str(e)}"
                    errors.append(error_msg)
                    if error_count <= 5:  # Only print first 5 errors
                        print(f"ERROR: {error_msg}")
            
            print(f"DEBUG: Final success_count = {success_count}, error_count = {error_count}")
            print(f"DEBUG: Total Performance records in DB = {Performance.objects.count()}")
        
        return {
            'success': True,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10],  # Limit to first 10 errors
            'deleted_count': deleted_count,
            'dataset_id': dataset.id
        }
        
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'errors': [f'Error processing file: {str(e)}']
        }


def validate_csv_structure(file):
    """
    Validate CSV structure before processing
    
    Args:
        file: Uploaded file object
    
    Returns:
        Dictionary with validation results
    """
    try:
        # Read file
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        else:
            return {
                'valid': False,
                'errors': ['Unsupported file format']
            }
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('_', '').str.replace(' ', '').str.lower()
        
        # Map columns
        column_mapping = {
            'studentid': 'student_id',
            'firstname': 'first_name',
            'lastname': 'last_name',
            'course': 'course_code',
            'coursecode': 'course_code',
            'score': 'score'
        }
        
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        
        # Check required columns (course_code is optional)
        required_columns = ['student_id', 'first_name', 'last_name', 'score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'valid': False,
                'errors': [f'Missing columns: {", ".join(missing_columns)}'],
                'columns_found': list(df.columns)
            }
        
        # Check data types
        errors = []
        
        # Validate scores are numeric
        try:
            pd.to_numeric(df['score'], errors='coerce')
        except:
            errors.append('Score column must contain numeric values')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'columns_found': list(df.columns),
            'row_count': len(df)
        }
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [str(e)]
        }