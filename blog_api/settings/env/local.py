from ..base import *
DEBUG = True

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}