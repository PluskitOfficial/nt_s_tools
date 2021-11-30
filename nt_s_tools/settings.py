import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(BASE_DIR))
SECRET_KEY = 'm-nu-@adw)zt!z)wrfk$4r*kjmb2@0#bcmr!jv6=64xvid*5g2'

DEBUG = False
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "tools",
]

MIDDLEWARE = [
    'nt_s_common.middleware.ResponseMiddleware',
]

ROOT_URLCONF = 'nt_s_tools.urls'
WSGI_APPLICATION = 'nt_s_tools.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nt_s_tools',
        'USER': os.getenv("MYSQL_USER"),
        'PASSWORD': os.getenv("MYSQL_PASSWORD"),
        'HOST': os.getenv("MYSQL_HOST"),
        'PORT': os.getenv("MYSQL_PORT"),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {'charset': 'utf8mb4'},
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        }
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False
STATIC_URL = '/static/'
logging.basicConfig(format='%(levelname)s:%(asctime)s %(pathname)s--%(funcName)s--line %(lineno)d-----%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.WARNING)
