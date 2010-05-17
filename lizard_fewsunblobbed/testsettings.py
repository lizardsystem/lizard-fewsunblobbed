DEBUG = True
TEMPLATE_DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db'
        },
    'fews-unblobbed': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testunblobbed.db'
        }
    }

SITE_ID = 1
INSTALLED_APPS = [
    'lizard_fewsunblobbed',
    'lizard_map',
    'lizard_ui',
    'staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    ]
ROOT_URLCONF = 'lizard_fewsunblobbed.urls'

# Used for django-staticfiles
STATIC_URL = '/static_media/'
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

DATABASE_ROUTERS = ['lizard_fewsunblobbed.routers.FewsUnblobbedRouter', ]

try:
    # Import local settings that aren't stored in svn.
    from lizard_fewsunblobbed.local_testsettings import *
except ImportError:
    pass
