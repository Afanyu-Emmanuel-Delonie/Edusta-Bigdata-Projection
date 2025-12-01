from django.core.management.base import BaseCommand
from performance.models import Performance


class Command(BaseCommand):
    help = 'Recalculate all student scores with correct formula'

    def handle(self, *args, **kwargs):
        performances = Performance.objects.all()
        total = performances.count()
        updated = 0
        
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"🔧 FIXING SCORES FOR {total} RECORDS")
        self.stdout.write(f"{'='*70}\n")
        
        for perf in performances:
            try:
                # Recalculate score correctly
                # Quiz1(5) + Quiz2(5) + Assignment(10) + Attendance(10) + Mid(30) + Final(40) = 100
                correct_score = (
                    float(perf.quiz1 or 0) +
                    float(perf.quiz2 or 0) +
                    float(perf.assignment or 0) +
                    float(perf.attendance or 0) +
                    float(perf.mid_semester or 0) +
                    float(perf.final_exam or 0)
                )
                
                # Cap at 100
                correct_score = min(correct_score, 100)
                
                # Update score
                old_score = perf.score
                perf.score = correct_score
                
                # Recalculate grade based on AUCA system
                if correct_score >= 85:
                    perf.grade = 'A'
                    perf.performance_status = 'Excellent'
                elif correct_score >= 80:
                    perf.grade = 'A-'
                    perf.performance_status = 'Excellent'
                elif correct_score >= 75:
                    perf.grade = 'B+'
                    perf.performance_status = 'Good'
                elif correct_score >= 70:
                    perf.grade = 'B'
                    perf.performance_status = 'Good'
                elif correct_score >= 65:
                    perf.grade = 'B-'
                    perf.performance_status = 'Good'
                elif correct_score >= 60:
                    perf.grade = 'C+'
                    perf.performance_status = 'Average'
                elif correct_score >= 55:
                    perf.grade = 'C'
                    perf.performance_status = 'Average'
                elif correct_score >= 50:
                    perf.grade = 'C-'
                    perf.performance_status = 'Average'
                elif correct_score >= 45:
                    perf.grade = 'D'
                    perf.performance_status = 'Poor'
                else:
                    perf.grade = 'F'
                    perf.performance_status = 'Poor'
                
                # Recalculate ML prediction
                if correct_score >= 50:
                    perf.ml_predicted_pass = True
                else:
                    perf.ml_predicted_pass = False
                
                # Set confidence based on how far from threshold
                distance_from_threshold = abs(correct_score - 50)
                perf.ml_confidence = min(50 + distance_from_threshold, 99)
                
                # Recalculate risk level
                if correct_score < 40:
                    perf.risk_level = 'CRITICAL'
                    perf.needs_intervention = True
                elif correct_score < 50:
                    perf.risk_level = 'HIGH'
                    perf.needs_intervention = True
                elif correct_score < 60:
                    perf.risk_level = 'MEDIUM'
                    perf.needs_intervention = False
                elif correct_score < 70:
                    perf.risk_level = 'LOW'
                    perf.needs_intervention = False
                else:
                    perf.risk_level = 'MINIMAL'
                    perf.needs_intervention = False
                
                perf.save()
                updated += 1
                
                if updated % 100 == 0:
                    self.stdout.write(f"  Processed {updated}/{total}...")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error updating {perf.id}: {str(e)}")
                )
        
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully updated {updated} records"))
        self.stdout.write(f"{'='*70}\n")
        
        # Show statistics
        total_students = Performance.objects.count()
        passed = Performance.objects.filter(score__gte=50).count()
        failed = Performance.objects.filter(score__lt=50).count()
        excellent = Performance.objects.filter(score__gte=85).count()
        good = Performance.objects.filter(score__gte=70, score__lt=85).count()
        average = Performance.objects.filter(score__gte=50, score__lt=70).count()
        poor = Performance.objects.filter(score__lt=50).count()
        
        self.stdout.write("\n📊 NEW STATISTICS:")
        self.stdout.write(f"  Total Students: {total_students}")
        self.stdout.write(f"  Passed (≥50): {passed} ({passed/total_students*100:.1f}%)")
        self.stdout.write(f"  Failed (<50): {failed} ({failed/total_students*100:.1f}%)")
        self.stdout.write(f"  Excellent (≥85): {excellent}")
        self.stdout.write(f"  Good (70-84): {good}")
        self.stdout.write(f"  Average (50-69): {average}")
        self.stdout.write(f"  Poor (<50): {poor}\n")