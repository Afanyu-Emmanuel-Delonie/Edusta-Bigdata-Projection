"""
Django Management Command: Run ML Predictions
File: performance/management/commands/run_ml_predictions.py

Usage:
    python manage.py run_ml_predictions
    python manage.py run_ml_predictions --semester "Fall 2024"
    python manage.py run_ml_predictions --course CS101
    python manage.py run_ml_predictions --department "Computer Science"
    python manage.py run_ml_predictions --generate-recommendations
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from performance.models import Performance, Semester, Course
from performance.ml_service import get_ml_service
from performance.recommendation_engine import get_recommendation_engine


class Command(BaseCommand):
    help = 'Run ML predictions on student performance data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--semester',
            type=str,
            help='Filter by semester name (e.g., "Fall 2024")',
        )
        
        parser.add_argument(
            '--course',
            type=str,
            help='Filter by course code (e.g., "CS101")',
        )
        
        parser.add_argument(
            '--department',
            type=str,
            help='Filter by student department',
        )
        
        parser.add_argument(
            '--student-id',
            type=str,
            help='Run prediction for specific student ID',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-run predictions even if already exist',
        )
        
        parser.add_argument(
            '--generate-recommendations',
            action='store_true',
            help='Also generate recommendations after predictions',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate without saving to database',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🤖 ML PREDICTION SERVICE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Initialize services
        ml_service = get_ml_service()
        if not ml_service.model_loaded:
            raise CommandError(
                '❌ ML model not loaded. Please ensure random_forest_passfail.pkl exists.'
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ ML Model loaded: {ml_service.MODEL_VERSION}'))
        
        # Build queryset with filters
        qs = Performance.objects.all().select_related('student', 'course', 'semester')
        
        if options['semester']:
            qs = qs.filter(semester__name__icontains=options['semester'])
            self.stdout.write(f"📅 Filter: Semester = {options['semester']}")
        
        if options['course']:
            qs = qs.filter(course__code__iexact=options['course'])
            self.stdout.write(f"📚 Filter: Course = {options['course']}")
        
        if options['department']:
            qs = qs.filter(student__department__iexact=options['department'])
            self.stdout.write(f"🏢 Filter: Department = {options['department']}")
        
        if options['student_id']:
            qs = qs.filter(student__student_id=options['student_id'])
            self.stdout.write(f"👤 Filter: Student ID = {options['student_id']}")
        
        # Filter out already predicted records unless --force
        if not options['force']:
            qs = qs.filter(ml_predicted_pass__isnull=True)
            self.stdout.write(f"🔄 Mode: Only new records (use --force to re-run)")
        else:
            self.stdout.write(f"⚡ Mode: Force re-run all predictions")
        
        total_records = qs.count()
        
        if total_records == 0:
            self.stdout.write(self.style.WARNING('\n⚠️  No records to process.'))
            return
        
        self.stdout.write(f"\n📊 Found {total_records} records to process\n")
        
        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN - No changes will be saved\n'))
        
        # Process predictions
        success_count = 0
        error_count = 0
        high_risk_count = 0
        intervention_count = 0
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting predictions...\n'))
        
        for idx, performance in enumerate(qs, 1):
            try:
                # Show progress
                if idx % 50 == 0 or idx == 1:
                    self.stdout.write(f"Processing {idx}/{total_records}...")
                
                # Run prediction
                prediction_results = ml_service.run_complete_prediction(performance)
                
                # Update performance record
                if not options['dry_run']:
                    for field, value in prediction_results.items():
                        if hasattr(performance, field):
                            setattr(performance, field, value)
                    performance.save()
                
                success_count += 1
                
                # Track statistics
                if prediction_results.get('risk_level') in ['CRITICAL', 'HIGH']:
                    high_risk_count += 1
                
                if prediction_results.get('needs_intervention'):
                    intervention_count += 1
                
                # Display high-risk students
                if prediction_results.get('risk_level') == 'CRITICAL':
                    self.stdout.write(
                        self.style.ERROR(
                            f"  🚨 CRITICAL: {performance.student.student_id} - "
                            f"{performance.course.code} (Score: {performance.score})"
                        )
                    )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ Error processing {performance.student.student_id}: {str(e)}"
                    )
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📈 PREDICTION RESULTS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f"✅ Successful predictions: {success_count}")
        self.stdout.write(f"❌ Errors: {error_count}")
        self.stdout.write(f"🔴 High-risk students: {high_risk_count}")
        self.stdout.write(f"⚠️  Intervention needed: {intervention_count}")
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Generate recommendations if requested
        if options['generate_recommendations'] and not options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\n🎯 Generating Recommendations...\n'))
            
            rec_engine = get_recommendation_engine()
            rec_stats = rec_engine.batch_generate_recommendations(qs, auto_save=True)
            
            self.stdout.write(self.style.SUCCESS('='*70))
            self.stdout.write(self.style.SUCCESS('📋 RECOMMENDATION RESULTS'))
            self.stdout.write(self.style.SUCCESS('='*70))
            self.stdout.write(f"📝 Total recommendations: {rec_stats['total_recommendations']}")
            self.stdout.write(f"🔴 High priority: {rec_stats['high_priority']}")
            self.stdout.write(f"👥 Students processed: {rec_stats['students_processed']}")
            self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        self.stdout.write(self.style.SUCCESS('✨ Done!\n'))