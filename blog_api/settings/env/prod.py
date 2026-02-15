from ..base import *
DEBUG = False

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
ALLOWED_HOSTS = ['www.example.com']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': BASE_DIR / 'db.postgres',
    }
}