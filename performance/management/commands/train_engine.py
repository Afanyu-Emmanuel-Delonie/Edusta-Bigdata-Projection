import os
from django.core.management.base import BaseCommand
from performance.ml_models.engine import EduStatEngine


class Command(BaseCommand):
    help = 'Trains the ML models using historical CSV data'

    def handle(self, *args, **options):
        path = 'historical_data.csv'
        if os.path.exists(path):
            engine = EduStatEngine(path)
            engine.train_models()
            self.stdout.write(self.style.SUCCESS('Models trained successfully!'))
        else:
            self.stdout.write(self.style.ERROR(f'File not found: {path}'))
