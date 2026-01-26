from django.core.management.base import BaseCommand
from analytics.ml_models.engine import EduStatEngine
import os

class Command(BaseCommand):
    help = 'Trains the AI models using historical CSV data'

    def handle(self, *args, **options):
        path = 'historical_data.csv' 
        if os.path.exists(path):
            engine = EduStatEngine(path)
            engine.train_models()
            self.stdout.write(self.style.SUCCESS('Successfully trained EduStat models!'))
        else:
            self.stdout.write(self.style.ERROR('Historical data file not found.'))