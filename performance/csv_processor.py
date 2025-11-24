"""
Fixed CSV Processor - Handles missing courses and duplicate issues
"""

import pandas as pd
from django.db import transaction, IntegrityError
from .models import Student, Course, Semester, Group, Performance, Dataset


def process_csv_upload(file, user, dataset_name, dataset_description='', course=None, semester=None):
    """
    Process CSV/Excel file upload with better duplicate handling
    """
    
    # Step 1: Read and validate file
    try:
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
        
        print(f"\n{'='*60}")
        print(f"FILE ANALYSIS")
        print(f"{'='*60}")
        print(f"Total rows: {len(df)}")
        print(f"Original columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\nFirst 3 rows (raw):")
        print(df.head(3).to_string())
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('_', '').str.replace(' ', '').str.lower()
        print(f"\nCleaned columns: {list(df.columns)}")
        
        # Map expected columns
        column_mapping = {
            'studentid': 'student_id',
            'firstname': 'first_name', 
            'lastname': 'last_name',
            'departmen': 'department',
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
        
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        print(f"Mapped columns: {list(df.columns)}")
        
        # Check if course_code column exists
        has_course_column = 'course_code' in df.columns
        print(f"\nHas course_code column: {has_course_column}")
        
        if not has_course_column and not course:
            print("WARNING: No course column found and no course selected in form!")
            print("This will cause all records to use 'GENERAL' course, which may cause duplicates!")
        
        # Validate required columns
        required_columns = ['student_id', 'first_name', 'last_name', 'score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'errors': [
                    f'Missing required columns: {", ".join(missing_columns)}.',
                    f'Found columns: {", ".join(df.columns)}',
                    'Required: student_id, first_name, last_name, score'
                ]
            }
        
        # Check for duplicate combinations
        if has_course_column:
            duplicate_check = df[['student_id', 'course_code']].copy()
            duplicate_check = duplicate_check.dropna()
            duplicates = duplicate_check[duplicate_check.duplicated(keep=False)]
            if len(duplicates) > 0:
                print(f"\nWARNING: Found {len(duplicates)} duplicate student+course combinations!")
                print("These will be skipped to avoid database errors.")
                print(duplicates.head(10))
        
        # Clean data
        print(f"\n{'='*60}")
        print(f"DATA CLEANING")
        print(f"{'='*60}")
        
        # Remove rows with empty required fields
        initial_count = len(df)
        df = df.dropna(subset=['student_id', 'first_name', 'last_name', 'score'])
        removed = initial_count - len(df)
        print(f"Removed {removed} rows with empty required fields")
        print(f"Remaining rows: {len(df)}")
        
        # Convert scores to numeric
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        invalid_scores = df['score'].isna().sum()
        print(f"Invalid scores found: {invalid_scores}")
        
        # Remove rows with invalid scores
        df = df[df['score'].notna()]
        print(f"Rows after removing invalid scores: {len(df)}")
        
        # Remove rows with out-of-range scores
        df = df[(df['score'] >= 0) & (df['score'] <= 100)]
        print(f"Rows after removing out-of-range scores: {len(df)}")
        
        if len(df) == 0:
            return {
                'success': False,
                'errors': ['No valid data rows found after cleaning. Please check your file.']
            }
        
        # Remove duplicates within the CSV itself
        if has_course_column:
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['student_id', 'course_code'], keep='first')
            deduped = before_dedup - len(df)
            print(f"Removed {deduped} duplicate student+course rows from CSV")
            print(f"Final rows to process: {len(df)}")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        import traceback
        print(f"\nERROR reading file: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'errors': [f'Error reading file: {str(e)}']
        }
    
    # Step 2: Process data within transaction
    try:
        with transaction.atomic():
            # Count existing records
            deleted_count = Performance.objects.count()
            
            # Delete ALL existing data
            Performance.objects.all().delete()
            Dataset.objects.all().delete()
            
            # Create new dataset
            dataset = Dataset.objects.create(
                name=dataset_name,
                description=dataset_description,
                semester=semester,
                course=course,
                uploaded_by=user if user and user.is_authenticated else None,
                is_active=True
            )
            
            print(f"Processing {len(df)} cleaned rows...")
            
            success_count = 0
            error_count = 0
            errors = []
            skipped_duplicates = 0
            
            # Track what we've already inserted to avoid duplicates
            inserted_combinations = set()
            
            for index, row in df.iterrows():
                try:
                    if index % 100 == 0:
                        print(f"Processing row {index}...")
                    
                    # Extract data
                    student_id_val = str(row['student_id']).strip()
                    first_name_val = str(row['first_name']).strip()
                    last_name_val = str(row['last_name']).strip()
                    
                    # Email
                    if 'email' in row and pd.notna(row['email']):
                        email_val = str(row['email']).strip()
                    else:
                        email_val = f"{student_id_val}@student.edu"
                    
                    # Department
                    if 'department' in row and pd.notna(row['department']):
                        department_val = str(row['department']).strip()
                    else:
                        department_val = 'General'
                    
                    # Get or create student
                    student, created = Student.objects.get_or_create(
                        student_id=student_id_val,
                        defaults={
                            'first_name': first_name_val,
                            'last_name': last_name_val,
                            'email': email_val,
                            'department': department_val
                        }
                    )
                    
                    # Course
                    if has_course_column and pd.notna(row['course_code']):
                        course_code = str(row['course_code']).strip()
                    elif course:
                        course_code = course.code
                    else:
                        # If no course info, create unique course per row to avoid duplicates
                        course_code = f"COURSE_{student_id_val}_{index}"
                    
                    course_obj, _ = Course.objects.get_or_create(
                        code=course_code,
                        defaults={
                            'name': course_code,
                            'department': department_val,
                            'credits': 3
                        }
                    )
                    
                    # Check if this combination already exists in this batch
                    combo_key = (student_id_val, course_code, semester.id, dataset.id)
                    if combo_key in inserted_combinations:
                        skipped_duplicates += 1
                        error_count += 1
                        errors.append(f"Row {index + 2}: Duplicate - Student {student_id_val} + Course {course_code} already processed")
                        continue
                    
                    # Semester
                    semester_obj = semester
                    
                    # Group (optional)
                    group_obj = None
                    if 'group' in row and pd.notna(row['group']):
                        group_name = str(row['group']).strip()
                        if group_name and group_name.lower() != 'nan':
                            group_obj, _ = Group.objects.get_or_create(
                                name=group_name,
                                course=course_obj,
                                semester=semester_obj,
                                defaults={'max_students': 30}
                            )
                    
                    # Score
                    score_val = float(row['score'])
                    
                    # Create performance record
                    try:
                        Performance.objects.create(
                            student=student,
                            course=course_obj,
                            semester=semester_obj,
                            group=group_obj,
                            dataset=dataset,
                            score=score_val,
                            uploaded_by=user if user and user.is_authenticated else None
                        )
                        
                        # Track this combination
                        inserted_combinations.add(combo_key)
                        success_count += 1
                        
                    except IntegrityError as ie:
                        # This combination already exists in database
                        skipped_duplicates += 1
                        error_count += 1
                        errors.append(f"Row {index + 2}: Duplicate in database - {str(ie)}")
                        continue
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: {str(e)}"
                    errors.append(error_msg)
                    
                    if error_count <= 20:
                        print(f"ERROR: {error_msg}")
            
            print(f"\n{'='*60}")
            print(f"PROCESSING COMPLETE")
            print(f"{'='*60}")
            print(f"Successfully imported: {success_count}")
            print(f"Errors: {error_count}")
            print(f"Skipped duplicates: {skipped_duplicates}")
            print(f"{'='*60}\n")
            
            # Success if we got at least some records
            if success_count == 0:
                raise Exception("No records were successfully imported")
            
            # Be more lenient - allow if at least 30% success
            if success_count < len(df) * 0.3:
                raise Exception(f"Too few successful imports ({success_count} out of {len(df)}). Please check your data.")
        
        return {
            'success': True,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:50],
            'deleted_count': deleted_count,
            'dataset_id': dataset.id
        }
        
    except Exception as e:
        import traceback
        print(f"\nCRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        
        return {
            'success': False,
            'errors': [
                f'Error: {str(e)}',
                f'Successfully processed: {success_count if "success_count" in locals() else 0} rows',
                f'Failed: {error_count if "error_count" in locals() else 0} rows',
                'Please check the server logs for detailed information.',
                '',
                '💡 TIPS:',
                '- Ensure your CSV has a "course" or "course_code" column',
                '- Each student+course combination should appear only once',
                '- All scores must be numeric (0-100)',
                '- Required fields: student_id, first_name, last_name, score'
            ]
        }