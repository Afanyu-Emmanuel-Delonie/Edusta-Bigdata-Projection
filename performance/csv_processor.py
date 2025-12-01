"""
Enhanced CSV Processor with ML Prediction Integration - FINAL VERSION
Handles semester matching and all edge cases
"""

import pandas as pd
from django.db import transaction, IntegrityError
from .models import Student, Course, Semester, Group, Performance, Dataset
from .ml_service import get_ml_service


def match_semester_from_csv(semester_string, default_semester):
    """
    Match CSV semester string to database Semester object
    CSV: "Semester 2 2024-2025" -> DB: "Semester 2"
    """
    if not semester_string or pd.isna(semester_string):
        return default_semester
    
    semester_str = str(semester_string).strip().lower()
    
    # Try to find matching semester
    if 'semester 1' in semester_str or 'sem 1' in semester_str:
        try:
            return Semester.objects.get(name='Semester 1')
        except Semester.DoesNotExist:
            pass
    
    if 'semester 2' in semester_str or 'sem 2' in semester_str:
        try:
            return Semester.objects.get(name='Semester 2')
        except Semester.DoesNotExist:
            pass
    
    if 'summer' in semester_str:
        try:
            return Semester.objects.get(name='Summer')
        except Semester.DoesNotExist:
            pass
    
    # If no match, return default
    return default_semester


def process_csv_with_ml_prediction(file, user, dataset_name, dataset_description='', course=None, semester=None, run_predictions=True):
    """
    Process CSV/Excel file upload with ML predictions
    
    Args:
        file: Uploaded file object
        user: Django User who uploaded
        dataset_name: Name for this dataset
        dataset_description: Optional description
        course: Course object (optional)
        semester: Semester object (required - used as default)
        run_predictions: Whether to run ML predictions (default True)
    
    Returns:
        Dictionary with success status, statistics, and errors
    """
    
    if not semester:
        return {
            'success': False,
            'errors': ['Semester is required for upload']
        }
    
    # Initialize ML service
    ml_service = get_ml_service() if run_predictions else None
    
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
        
        print(f"\n{'='*70}")
        print(f"📊 FILE ANALYSIS - ML ENHANCED PROCESSING")
        print(f"{'='*70}")
        print(f"Total rows: {len(df)}")
        print(f"Original columns: {list(df.columns)}")
        
        # Clean column names - keep underscores but standardize
        df.columns = df.columns.str.strip().str.lower()
        
        # Enhanced column mapping for all score components
        column_mapping = {
            # Student info
            'student_id': 'student_id',
            'studentid': 'student_id',
            'first_name': 'first_name',
            'firstname': 'first_name', 
            'last_name': 'last_name',
            'lastname': 'last_name',
            'departmen': 'department',  # Handle typo in CSV
            'department': 'department',
            'email': 'email',
            
            # Course info
            'course': 'course_code',
            'course_code': 'course_code',
            'coursecode': 'course_code',
            'group': 'group',
            'semester': 'semester_name',
            
            # Score components
            'quiz1': 'quiz1',
            'quiz_1': 'quiz1',
            'quiz2': 'quiz2',
            'quiz_2': 'quiz2',
            'assignment': 'assignment',
            'assignments': 'assignment',
            'attendance': 'attendance',
            'mid_semester': 'mid_semester',
            'midsemester': 'mid_semester',
            'midterm': 'mid_semester',
            'mid_exam': 'mid_semester',
            'midexam': 'mid_semester',
            'final_exam': 'final_exam',
            'finalexam': 'final_exam',
            'final': 'final_exam',
            'other': 'other_total',
            
            # Calculated/legacy
            'score': 'final_score',
            'total_score': 'final_score',
            'totalscore': 'final_score',
            'grade': 'grade',
            'ranking': 'ranking',
        }
        
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        print(f"Mapped columns: {list(df.columns)}")
        
        # Validate required columns
        required_columns = ['student_id', 'first_name', 'last_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'errors': [
                    f'Missing required columns: {", ".join(missing_columns)}.',
                    f'Found columns: {", ".join(df.columns)}',
                    'Required: student_id, first_name, last_name'
                ]
            }
        
        # Check which score components are available
        score_components = ['quiz1', 'quiz2', 'assignment', 'attendance', 'mid_semester', 'final_exam']
        available_components = [col for col in score_components if col in df.columns]
        
        print(f"\n📋 Available score components: {available_components}")
        
        # Check if we have other_total column
        has_other_total = 'other_total' in df.columns
        
        if len(available_components) == 0 and 'final_score' not in df.columns and not has_other_total:
            return {
                'success': False,
                'errors': [
                    'No score data found!',
                    'CSV must contain either:',
                    '  - Score components (quiz1, quiz2, assignment, attendance, mid_semester, final_exam)',
                    '  - Or a final_score column',
                    '  - Or an other column'
                ]
            }
        
        # Clean data
        print(f"\n{'='*70}")
        print(f"🧹 DATA CLEANING")
        print(f"{'='*70}")
        
        initial_count = len(df)
        df = df.dropna(subset=['student_id', 'first_name', 'last_name'])
        removed = initial_count - len(df)
        print(f"Removed {removed} rows with empty required fields")
        
        # Convert score columns to numeric
        for col in available_components + ['final_score', 'other_total']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with ALL scores missing
        score_cols = available_components if available_components else (['final_score'] if 'final_score' in df.columns else ['other_total'])
        df = df.dropna(subset=score_cols, how='all')
        print(f"Rows after removing all-missing scores: {len(df)}")
        
        print(f"Final rows to process: {len(df)}")
        print(f"{'='*70}\n")
        
        if len(df) == 0:
            return {
                'success': False,
                'errors': ['No valid data rows found after cleaning.']
            }
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR reading file: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'errors': [f'Error reading file: {str(e)}']
        }
    
    # Step 2: Process data with ML predictions
    try:
        with transaction.atomic():
            # DON'T delete old data - just add new records
            # This was causing issues with the unique constraint
            
            # Handle missing course - make it nullable
            has_course_column = 'course_code' in df.columns
            dataset_course = course
            if dataset_course is None and has_course_column and df['course_code'].notna().any():
                # Get first valid course from CSV
                first_course = str(df['course_code'].dropna().iloc[0]).strip()
                dataset_course, _ = Course.objects.get_or_create(
                    code=first_course,
                    defaults={
                        'name': first_course,
                        'department': 'General',
                        'credits': 3
                    }
                )
            
            # Create new dataset
            dataset = Dataset.objects.create(
                name=dataset_name,
                description=dataset_description,
                semester=semester,
                course=dataset_course,
                uploaded_by=user if user and user.is_authenticated else None,
                is_active=True
            )
            
            print(f"\n{'='*70}")
            print(f"🤖 PROCESSING WITH ML PREDICTIONS")
            print(f"{'='*70}")
            
            success_count = 0
            error_count = 0
            errors = []
            ml_predictions_count = 0
            high_risk_count = 0
            intervention_needed_count = 0
            
            inserted_combinations = set()
            
            for index, row in df.iterrows():
                try:
                    if index % 50 == 0:
                        print(f"Processing row {index + 1}/{len(df)}...")
                    
                    # Extract student data
                    student_id_val = str(row['student_id']).strip()
                    first_name_val = str(row['first_name']).strip()
                    last_name_val = str(row['last_name']).strip()
                    
                    # Email
                    email_val = str(row['email']).strip() if 'email' in row and pd.notna(row['email']) else f"{student_id_val}@student.edu"
                    
                    # Department
                    department_val = str(row['department']).strip() if 'department' in row and pd.notna(row['department']) else 'General'
                    
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
                    
                    # Update student info if exists but data changed
                    if not created:
                        student.first_name = first_name_val
                        student.last_name = last_name_val
                        student.email = email_val
                        student.department = department_val
                        student.save()
                    
                    # Course
                    if has_course_column and pd.notna(row['course_code']):
                        course_code = str(row['course_code']).strip()
                    elif course:
                        course_code = course.code
                    else:
                        course_code = f"COURSE_{index}"
                    
                    course_obj, _ = Course.objects.get_or_create(
                        code=course_code,
                        defaults={
                            'name': course_code,
                            'department': department_val,
                            'credits': 3
                        }
                    )
                    
                    # Match semester from CSV (if semester_name column exists)
                    row_semester = semester  # Default
                    if 'semester_name' in row and pd.notna(row['semester_name']):
                        row_semester = match_semester_from_csv(row['semester_name'], semester)
                    
                    # Check for duplicates in this batch
                    combo_key = (student_id_val, course_code, row_semester.id, dataset.id)
                    if combo_key in inserted_combinations:
                        error_count += 1
                        errors.append(f"Row {index + 2}: Duplicate in this upload")
                        continue
                    
                    # Check database for existing record
                    if Performance.objects.filter(
                        student=student,
                        course=course_obj,
                        semester=row_semester,
                        dataset=dataset
                    ).exists():
                        error_count += 1
                        errors.append(f"Row {index + 2}: Already exists in database")
                        continue
                    
                    # Group (optional)
                    group_obj = None
                    if 'group' in row and pd.notna(row['group']):
                        group_name = str(row['group']).strip()
                        if group_name and group_name.lower() != 'nan':
                            group_obj, _ = Group.objects.get_or_create(
                                name=group_name,
                                course=course_obj,
                                semester=row_semester,
                                defaults={'max_students': 30}
                            )
                    
                    # Extract score components with defaults
                    quiz1_val = float(row.get('quiz1', 0)) if pd.notna(row.get('quiz1')) else 0
                    quiz2_val = float(row.get('quiz2', 0)) if pd.notna(row.get('quiz2')) else 0
                    assignment_val = float(row.get('assignment', 0)) if pd.notna(row.get('assignment')) else 0
                    attendance_val = float(row.get('attendance', 0)) if pd.notna(row.get('attendance')) else 0
                    mid_semester_val = float(row.get('mid_semester', 0)) if pd.notna(row.get('mid_semester')) else 0
                    final_exam_val = float(row.get('final_exam', 0)) if pd.notna(row.get('final_exam')) else 0
                    
                    # Calculate or get other_total
                    # Calculate or get other_total
                    if has_other_total and pd.notna(row.get('other_total')):
                        other_total_val = float(row['other_total'])
                    else:
                        other_total_val = quiz1_val + quiz2_val + assignment_val + attendance_val

                    # Calculate final score if not provided
                    if 'final_score' in row and pd.notna(row['final_score']):
                        final_score_val = float(row['final_score'])
                    else:
                        # CORRECT: Simply sum all components
                        # Quiz1(5) + Quiz2(5) + Assignment(10) + Attendance(10) + Mid(30) + Final(40) = 100
                        final_score_val = other_total_val + mid_semester_val + final_exam_val
                        final_score_val = min(final_score_val, 100)  # Cap at 100  
                        # Create performance record
                        
                        
                    try:
                        performance = Performance.objects.create(
                            student=student,
                            course=course_obj,
                            semester=row_semester,
                            group=group_obj,
                            dataset=dataset,
                            
                            # Score components
                            quiz1=quiz1_val,
                            quiz2=quiz2_val,
                            assignment=assignment_val,
                            attendance=attendance_val,
                            mid_semester=mid_semester_val,
                            final_exam=final_exam_val,
                            
                            # Calculated
                            other_total=other_total_val,
                            score=final_score_val,
                            
                            uploaded_by=user if user and user.is_authenticated else None
                        )
                        
                        # Run ML prediction if enabled
                        if run_predictions and ml_service and ml_service.model_loaded:
                            try:
                                ml_service.update_performance_with_prediction(performance, save=True)
                                ml_predictions_count += 1
                                
                                # Track high-risk students
                                if performance.risk_level in ['CRITICAL', 'HIGH']:
                                    high_risk_count += 1
                                
                                if performance.needs_intervention:
                                    intervention_needed_count += 1
                                
                            except Exception as ml_error:
                                print(f"⚠️ ML prediction failed for row {index + 1}: {str(ml_error)}")
                        
                        # Track successful insertion
                        inserted_combinations.add(combo_key)
                        success_count += 1
                        
                    except IntegrityError as ie:
                        error_count += 1
                        errors.append(f"Row {index + 2}: Constraint violation - {str(ie)[:100]}")
                        continue
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: {str(e)[:150]}"
                    errors.append(error_msg)
                    
                    # Print first 20 errors in detail
                    if error_count <= 20:
                        print(f"❌ ERROR: {error_msg}")
            
            print(f"\n{'='*70}")
            print(f"✅ PROCESSING COMPLETE")
            print(f"{'='*70}")
            print(f"Successfully imported: {success_count}")
            print(f"ML predictions generated: {ml_predictions_count}")
            print(f"High-risk students identified: {high_risk_count}")
            print(f"Students needing intervention: {intervention_needed_count}")
            print(f"Errors: {error_count}")
            print(f"{'='*70}\n")
            
            # Relaxed success criteria - accept if at least some records imported
            if success_count == 0:
                raise Exception("No records were successfully imported")
        
        return {
            'success': True,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:100],  # Return more errors for debugging
            'dataset_id': dataset.id,
            
            # ML Statistics
            'ml_enabled': run_predictions and ml_service and ml_service.model_loaded,
            'ml_predictions_count': ml_predictions_count,
            'high_risk_count': high_risk_count,
            'intervention_needed_count': intervention_needed_count,
            'ml_model_version': ml_service.MODEL_VERSION if ml_service else None,
        }
        
    except Exception as e:
        import traceback
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        
        return {
            'success': False,
            'errors': [
                f'Error: {str(e)}',
                f'Successfully processed: {success_count if "success_count" in locals() else 0} rows',
                f'Failed: {error_count if "error_count" in locals() else 0} rows',
            ] + (errors[:20] if 'errors' in locals() else [])
        }


# Alias for backward compatibility
process_csv_upload = process_csv_with_ml_prediction