# local_settings.py used in k8s-deployed CommonsShare. In a manually deployed CommonsShare,
# a backup copy of this file specific to the deployment environment should be used.

import os
from kombu import Queue, Exchange

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY', '')
NEVERCACHE_KEY = os.environ.get('NEVERCACHE_KEY', '')

ALLOWED_HOSTS = [
    '*'
]

# for Django/Mezzanine comments and ratings to require user login
COMMENTS_ACCOUNT_REQUIRED = True
RATINGS_ACCOUNT_REQUIRED = True
COMMENTS_USE_RATINGS = True

RABBITMQ_HOST = os.environ.get('RABBITMQ_PORT_5672_TCP_ADDR', 'localhost')
RABBITMQ_PORT = '5672'

POSTGIS_HOST = os.environ.get('POSTGIS_PORT_5432_TCP_ADDR', 'localhost')
POSTGIS_PORT = 5432
POSTGIS_DB = os.environ.get('POSTGIS_DB', 'postgres')
POSTGIS_PASSWORD = os.environ.get('POSTGIS_PASSWORD', 'postgres')
POSTGIS_USER = os.environ.get('POSTGIS_USER', 'postgres')

# celery settings
# customizations: we need a special queue for broadcast signals to all
# docker daemons.  we also need a special queue for direct messages to all
# docker daemons.
BROKER_URL='amqp://guest:guest@{RABBITMQ_HOST}:{RABBITMQ_PORT}//'.format(RABBITMQ_HOST=RABBITMQ_HOST, RABBITMQ_PORT=RABBITMQ_PORT)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_DEFAULT_QUEUE = 'default'
DEFAULT_EXCHANGE=Exchange('default', type='topic')

CELERY_QUEUES = (
    Queue('default', DEFAULT_EXCHANGE, routing_key='task.default'),
)
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERY_ROUTES = ('hs_core.router.HSTaskRouter',)


USE_SOUTH = False
SITE_TITLE = "CommonsShare"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
WHITE_LIST_LOGIN = False
WHITE_LIST_EMAIL = "protocopdgenehelp@lists.renci.org"

#############
# DATABASES #
#############

DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        # DB name or path to database file if using sqlite3.
        "NAME": POSTGIS_DB,
        # Not used with sqlite3.
        "USER": POSTGIS_USER,
        # Not used with sqlite3.
        "PASSWORD": POSTGIS_PASSWORD,
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": POSTGIS_HOST,
        # Set to empty string for default. Not used with sqlite3.
        "PORT": POSTGIS_PORT,
    }
}
POSTGIS_VERSION=(2,1,1)

# Local resource iRODS configuration
USE_IRODS = False
FILE_SYSTEM_ROOT = '/tmp'
IRODS_ROOT = '/tmp'
IRODS_ICOMMANDS_PATH = '/usr/bin'
IRODS_HOST = ''
IRODS_PORT = '1247'
IRODS_DEFAULT_RESOURCE = ''
IRODS_HOME_COLLECTION = ''
IRODS_CWD = ''
IRODS_ZONE = ''
IRODS_USERNAME = ''
IRODS_AUTH = ''
IRODS_GLOBAL_SESSION = True

# bag path and postfix
BAGIT_PATH = 'bags'
BAGIT_POSTFIX = 'zip'

OAUTH_SERVICE_SERVER_URL = os.environ.get('OAUTH_SERVICE_SERVER_URL', '')
OAUTH_APP_KEY = os.environ.get('OAUTH_APP_KEY', '')
DATA_REG_SERVICE_SERVER_URL = OAUTH_SERVICE_SERVER_URL
DATA_REG_API_KEY = os.environ.get('DATA_REG_API_KEY', '')

DOI_OAUTH_TOKEN = os.environ.get('DOI_OAUTH_TOKEN', '')
DOI_PUT_URL = 'https://ors.test.datacite.org/doi/put?code='
FAIRSHAKE_URL = 'https://fairshake.cloud'
FAIRSHAKE_USERID = 'bot.commonsshare@gmail.com'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_USER = 'bot.commonsshare@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'bot.commonsshare@gmail.com'
DEFAULT_SUPPORT_EMAIL = 'bot.commonsshare@gmail.com'

HYDROSHARE_SHARED_TEMP = '/shared_tmp'

TIME_ZONE = "Etc/UTC"

# full text search URL
FTS_URL = ""

# trusted servers that need user's access token for user authentication
TRUSTED_SERVERS = (
    'apps.commonsshare.org',
    'copdgenejupyterlaunchergpu.commonsshare.org',
    'copdgenejupyterlauncher.commonsshare.org',
)
