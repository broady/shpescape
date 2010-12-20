#Please create a local_settings.py which should include, at least:
# - ADMINS
# - DEFAULT_FROM_EMAIL
# - DATABASES
# - SECRET_KEY
# - FT_DOMAIN_KEY
# - FT_DOMAIN_SECRET
# - EMAIL_HOST
# - EMAIL_HOST_USER
# - EMAIL_HOST_PASSWORD
# - EMAIL_PORT
# - EMAIL_USE_TLS


import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')
SHP_UPLOAD_DIR = '/tmp/'

ADMINS = (
    ('Admin1', 'your_email_address'),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'your_email_addressm'
EMAIL_MANAGERS = False

CACHE_BACKEND = 'file:///tmp/shapeft_cache'

DATABASE_NAME = 'shapeft'

DATABASES = {
    'default': {
        'NAME': DATABASE_NAME,
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'postgres',
        'PASSWORD': 'foo'
    }
}

TIME_ZONE = 'America/Vancouver'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/admin_media/'

SECRET_KEY = 'store-in-local-settings'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.csrf.middleware.CsrfViewMiddleware',
    'django.contrib.csrf.middleware.CsrfResponseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'django.contrib.gis',
    'django.contrib.humanize',
    'django.contrib.webdesign',
    'shapeft',
    'shapes',
    'contact',
    'ft_auth',
)

FT_DOMAIN_KEY = 'shpescape.com'
FT_DOMAIN_SECRET = 'foo'


try:
    from local_settings import *
except ImportError, exp:
    pass
