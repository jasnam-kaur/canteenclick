# canteenclick/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteenclick.settings')

application = get_wsgi_application()

# If you use whitenoise, you might also have this line, which is good practice:
from whitenoise.django import DjangoWhiteNoise
application = DjangoWhiteNoise(application)