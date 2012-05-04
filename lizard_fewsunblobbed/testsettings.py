import os

from lizard_ui.settingshelper import setup_logging
from lizard_ui.settingshelper import STATICFILES_FINDERS

DEBUG = True
TEMPLATE_DEBUG = True

# SETTINGS_DIR allows media paths and so to be relative to this settings file
# instead of hardcoded to c:\only\on\my\computer.
SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

# BUILDOUT_DIR is for access to the "surrounding" buildout, for instance for
# BUILDOUT_DIR/var/static files to give django-staticfiles a proper place
# to place all collected static files.
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
LOGGING = setup_logging(BUILDOUT_DIR)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': 'test.db',
        },
    'fews-unblobbed': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testunblobbed.db',
        }
    }

SITE_ID = 1
INSTALLED_APPS = [
    'lizard_fewsunblobbed',
    'lizard_map',
    'lizard_ui',
    'django_extensions',
    'compressor',
    'staticfiles',
    'django_nose',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.gis',
    ]
ROOT_URLCONF = 'lizard_fewsunblobbed.urls'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Used for django-staticfiles
STATIC_URL = '/static_media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
MEDIA_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'media')
STATICFILES_FINDERS = STATICFILES_FINDERS

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default items.
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    # Needs to be added for django-staticfiles to allow you to use
    # {{ STATIC_URL }}myapp/my.css in your templates.
    'staticfiles.context_processors.static_url',
    )

# We switch off compression so that the automated tests also can get the full
# javascript.
COMPRESS_ENABLED = False
COMPRESS_ROOT = STATIC_URL

DATABASE_ROUTERS = ['lizard_fewsunblobbed.routers.FewsUnblobbedRouter', ]

try:
    # Import local settings that aren't stored in svn.
    from lizard_fewsunblobbed.local_testsettings import *
except ImportError:
    pass
