import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .settings.production import *
else:
    from .settings.development import *
