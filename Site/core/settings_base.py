# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project.

    For more information on this file, see
    https://docs.djangoproject.com/en/5.2/topics/settings/

    For the full list of settings and their values, see
    https://docs.djangoproject.com/en/5.2/ref/settings/

    this file is included by django.conf.settings

    Normal:       (wsgi.py or ./manage.py cmd)
      Site/settings.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings  <-- replaced on real deployment
          provides additional items that are part of the release

    Autotest via test.sh  (uses ./manage.py cmd --settings=Site.settings_autotest)
      Site/settings_autotest[_nodebug].py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
          provides additional items that are part of the release
      provides changes to to settings for autotest

    Dev server via run.sh  (uses ./manage.py cmd --settings=Site.settings_dev)
      Site/settings_dev.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
          provides additional items that are part of the release
      provides changes to to settings for dev
"""

import os

# implementation uses this instead of built-in default, to allow override during autotest/dev
# None = use built-in default
BETAAL_API_URL = None

# ability to override the server URL for test purposes
# None = use built-in default
GOOGLEMAPS_API_URL = None

# toon het kaartje Ledenvoordeel?
TOON_LEDENVOORDEEL = True


# import install-specific settings from a separate file
# that is easy to replace as part of the deployment process
from Site.settings_local import *       # noqa


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJ_DIR)
APPS_DIR = os.path.dirname(BASE_DIR)

# version of the site
# this is used to keep site feedback separated by version
SITE_VERSIE = '2026-08-31'

# modules van de site
INSTALLED_APPS = [
    'Beheer.apps.BeheerConfig',         # must go first: provides admin template override
    'Beheer.apps.BeheerAdminConfig',    # uitbreiding op admin interface
    'Account',
    'BasisTypen',
    'Bestelling',
    'Betaal',
    'Bondspas',
    'Competitie',
    'CompBeheer',
    'CompInschrijven',
    'CompKampioenschap',
    'CompLaagBond',
    'CompLaagRegio',
    'CompLaagRayon',
    'CompScores',
    'CompUitslagen',
    'DataApi',
    'Design',
    'Evenement',
    'Feedback',
    'Functie',
    'Geo',
    'GoogleDrive',
    'GraphDrive',
    'HistComp',
    'ImportCRM',
    'Instaptoets',
    'Kalender',
    'Locatie',
    'Ledenvoordeel',
    'Logboek',
    'Mailer',
    'Opleiding',
    'Overig',
    'Plein',
    'Privacy',
    'Records',
    'Registreer',
    'Score',
    'Scheidsrechter',
    'SiteMap',
    'Spelden',
    'Sporter',
    'Taken',
    'TijdelijkeCodes',
    'Vereniging',
    'Webwinkel',
    'Wedstrijden',
    'WedstrijdInschrijven',
    'django.contrib.staticfiles',   # gather static files from modules helper + serve static files in dev
    'django.contrib.sessions',      # support for database-backed sessions; needed for logged-in user
    'django.contrib.auth',          # authenticatie framework
    'django.contrib.contenttypes',  # permission association to models
    'django.contrib.messages',
]


# AuthenticationMiddleware must be after SessionMiddleware
#        MessageMiddleware must be after SessionMiddleware
#
# SecurityMiddleware provides:  (see https://docs.djangoproject.com/en/5.2/ref/middleware/)
# - Strict-Transport-Security header (max-age = settings.SECURE_HSTS_SECONDS)
# - Referrer-Policy header (='same-origin')
# - Cross-Origin-Opener-Policy header (='same-origin')
# - X-Content-Type-Options header (='nosniff')
#
# TODO: ContentSecurityPolicyMiddleware provides: (see https://docs.djangoproject.com/en/6.0/ref/csp/)
# - Content-Security-Policy header ('default-src=self')
# voorlopig geregeld via webserver header
#
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',                # security (https improvements)
    'django.contrib.sessions.middleware.SessionMiddleware',         # manage sessions across requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',      # geeft request.user
    'django.middleware.common.CommonMiddleware',                    # adds Content-Length http header + append slash
    'django.middleware.csrf.CsrfViewMiddleware',                    # security (cross-site request forgery)
    'django.contrib.messages.middleware.MessageMiddleware',         # mandatory for admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',       # security: ask browser to deny (i)frame embedding
    'Account.middleware.HerhaalLoginOTP',                           # forceer nieuwe login en otp controles
]


# gebruik ingebouwde authenticatie / login laag
# inclusief permissions en groepen
# levert ook de integratie met sessies
# en het niet accepteren van oude sessies na wachtwoord wijziging
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend'
]


# vervanger van (aanpassing/uitbreiding op) de ingebouwde User
AUTH_USER_MODEL = 'Account.Account'

# maximum aantal keer dat een verkeerd wachtwoord opgegeven mag worden
# voor een account (login of wijzig-wachtwoord) voor het geblokkeerd wordt
AUTH_BAD_PASSWORD_LIMIT = 5
AUTH_BAD_PASSWORD_LOCKOUT_MINS = 15


# templates (django template language) processors
TEMPLATES = [
    {
        'NAME': 'dtl_loader',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [ str(APPS_DIR.path('templates')), ],
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # 'django.template.context_processors.debug',             # adds 'debug' and 'sql_queries'

                # request, auth and messages are required for the admin interface
                'django.template.context_processors.request',           # adds 'request'
                'django.contrib.auth.context_processors.auth',          # adds 'user' and 'perms
                'django.contrib.messages.context_processors.messages',  # adds 'messages' and 'DEFAULT_MESSAGE_LEVELS'

                'Design.context_processors.site_layout',                # voor het menu en de fonts
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', ['Site.core.minify_dtl.Loader']),
            ],
        },
    },
]

# avoid conflicts with other Django applications
SESSION_COOKIE_NAME = 'mh_session_id'
CSRF_COOKIE_NAME = 'mh_csrf_token'

# point out location of WSGI application for django runserver command
WSGI_APPLICATION = 'Site.core.wsgi.application'

# let browsers remember to connect with https
# security analysis recommends at least 365 days
SECURE_HSTS_SECONDS = 34567890      # 34567890 = 400 days


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# herhaal intervallen voorkomen lang misbruik van een gekopieerde cookie
HERHAAL_INTERVAL_LOGIN = 21     # elke 21 dagen opnieuw inloggen
HERHAAL_INTERVAL_OTP = 7        # elke 7 dagen opnieuw OTP controle

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'nl-NL'     # provides wanted date/time output format
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True

# sla alle datums in de database op als UTC
# dit doet PostgreSQL sowieso, onafhankelijk van deze instelling        # noqa
# alleen vertalen bij presentatie naar de gebruiker toe
USE_TZ = True


# top-level URL-verdeling naar apps
ROOT_URLCONF = 'Site.core.urls'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/mh-static/'          # url where the server is serving the files
STATIC_ROOT = 'Site/.static'        # relative to project top-dir
STATICFILES_DIRS = [
    ("webwinkel_fotos", WEBWINKEL_FOTOS_DIR),       # noqa
    ("pdfs", STATIC_PDFS_DIR),
]
STATICFILES_FINDERS = [
    'Site.core.transpose_js.AppJsFinder',                       # create static files from .js + minify/instrument
    'django.contrib.staticfiles.finders.FileSystemFinder',      # zoekt in STATICFILES_DIRS
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # zoekt in App/static/
]

STORAGES = {
    # "default": {
    #     "BACKEND": "django.core.files.storage.FileSystemStorage"
    # },
    "staticfiles": {
        "BACKEND": "Site.core.static.MHManifestStaticFilesStorage",       # static files krijgen ook hash in de naam
    }
}

# wordt gebruikt door LoginView als er geen 'next' veld bij de POST zit
# LOGIN_REDIRECT_URL = '/plein/'

# wordt gebruikt door de permission_required decorator en UserPassesTextMixin
# om de gebruiker door te sturen als een view geen toegang verleend
LOGIN_URL = '/account/login/'


# for debug_toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

# globale keuze voor automatische primary keys
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# interface naar achtergrondtaken
BACKGROUND_SYNC_POORT = 3000
BACKGROUND_SYNC__COMPETITIE_MUTATIES = BACKGROUND_SYNC_POORT + 1
BACKGROUND_SYNC__BONDSPAS_DOWNLOADER = BACKGROUND_SYNC_POORT + 2
BACKGROUND_SYNC__BESTEL_MUTATIES = BACKGROUND_SYNC_POORT + 3
BACKGROUND_SYNC__BETAAL_MUTATIES = BACKGROUND_SYNC_POORT + 4
BACKGROUND_SYNC__SCHEIDS_MUTATIES = BACKGROUND_SYNC_POORT + 5

# our own test runner that executes the tests ordered by application hierarchy indicators to ensure that
# low-level errors are reported before applications depending that (broken) functionality report failures
TEST_RUNNER = 'TestHelpers.app_hierarchy_testrunner.HierarchyRunner'

# applicatie specifieke settings
MINIMUM_LEEFTIJD_LID = 5

# minimum aantal scores in uitslag vorige seizoen nodig om te gebruiken als AG voor nieuwe seizoen
COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG = 6
COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG = 6
INTERLAND_25M_MINIMUM_SCORES_VOOR_DEELNAME = 6

# week waarin de laatste wedstrijden geschoten mogen worden
COMPETITIES_START_WEEK = 37
COMPETITIE_18M_LAATSTE_WEEK = 50        # week 37 t/m week 50
COMPETITIE_25M_LAATSTE_WEEK = 7         # week 37 t/m week 7

COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER = 4*7      # open 4 weeks after start week

COMPETITIE_18M_INDIV_LIMIETEN = (24, 20, 16, 12, 8, 4)
COMPETITIE_25M_INDIV_LIMIETEN = (64, 56, 52, 48, 44, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4)

# maximum aantal resultaten dat een doorzoeking van de records terug geeft
# dit voorkomt honderden resultaten bij het zoeken naar de letter e
# 150 omdat bepaalde plaatsen veel records hebben, zoals Schijndel (93 in Okt 2019)
RECORDS_MAX_ZOEKRESULTATEN = 150

# de mogelijke waarden voor soort_record in de administratie van de NL records
# wordt gebruikt om invoerfouten te ontdekken en rapporteren
RECORDS_TOEGESTANE_SOORTEN = (

    # LET OP: dit is ook meteen de presentatie-volgorde van de records

    # Outdoor
    'WA1440',
    'WA1440 dubbel',
    '30m',
    '30m (72p)',        # alleen voor VI
    '30m (144p)',       # alleen voor VI
    '40m',
    '50m',  # 36p
    '50m (72p)',
    '50m (144p)',
    '60m',  # 36p
    '60m (72p)',        # 60m ronde
    '60m (144p)',       # dubbele 60m ronde --> voor Onder 18 en 50+
    '70m',  # 36p
    '70m (72p)',        # 70m ronde
    '70m (144p)',       # dubbele 70m ronde
    '90m',  # 36p
    '50m (15p)',
    '60m (12p)',
    '70m (12p)',
    '50m (122cm)',

    # Outdoor, FUTURE: still to be cleaned up
    'ShortMetric',

    # indoor
    '18m (60p)',
    '18m',
    '18m (15p)',
    '18m (12p)',
    '25m (60p)',
    '25m',
    '25m+18m (120p)',
    '25m+18m (60p)',

    # 25m1pijl
    '50p',
    '30p',
)


# let op: in sync houden met para2url in Records/views_indiv.py
RECORDS_TOEGESTANE_PARA_KLASSEN = (
    "Open",
    "Staand",       # tot 2014-04-01
    "W1",
    "W2",           # tot 2014-04-01
    "VI1",          # sinds 2014-04-01
    "VI2/3"         # sinds 2014-04-01
    # andere historische record typen zijn niet in gebruik dus niet in dit lijstje
)

CRM_IMPORT_SPELDEN_VERTAAL_PAS_CODE = {
    # ster spelden cadet/master --> zilveren ster
    'RC1000': 'R1000Z',
    'RC1100': 'R1100Z',
    'RC1200': 'R1200Z',
    'RC1300': 'R1300Z',
    'RC1350': 'R1350Z',
    'RC1400': 'R1400Z',

    'RM1000': 'R1000Z',
    'RM1100': 'R1100Z',
    'RM1200': 'R1200Z',
    'RM1300': 'R1300Z',
    'RM1350': 'R1350Z',
    'RM1400': 'R1400Z',

    'CC1000': 'C1000Z',
    'CC1100': 'C1100Z',
    'CC1200': 'C1200Z',
    'CC1300': 'C1300Z',
    'CC1350': 'C1350Z',
    'CC1400': 'C1400Z',

    'CM1000': 'C1000Z',
    'CM1100': 'C1100Z',
    'CM1200': 'C1200Z',
    'CM1300': 'C1300Z',
    'CM1350': 'C1350Z',
    'CM1400': 'C1400Z',

    # target awards oude naar nieuwe code
    'WA Wit': 'TA-WIT',
    'WA Zwart': 'TA-ZWART',
    'WA Blauw': 'TA-BLAUW',
    'WA Rood': 'TA-ROOD',
    'WA Goud': 'TA-GOUD',
    'WA Purper': 'TA-PURPER',

    # arrowhead oude naar nieuwe code
    'GROEN': 'AH-GROEN',
    'BRUIN': 'AH-BRUIN',
    'GRIJS': 'AH-GRIJS',
    'ZWART': 'AH-ZWART',
    'WIT': 'AH-WIT',
    'ZILVER': 'AH-ZILVER',
    'GOUD': 'AH-GOUD',

    'GROEN24': 'AH24-GROEN',
    'GRIJS24': 'AH24-GRIJS',
    'WIT24': 'AH24-WIT',
    'ZWART24': 'AH24-ZWART',
    'GOUD24': 'AH24-GOUD',
}

OPLEIDING_CODES = (
    # code, afk-voor-pas, beschrijving, hogere-opleidingen
    ('011', 'HBT-A', 'Handboogtrainer A', ('014', '015')),
    ('012', 'HBT-B', 'Handboogtrainer B', ('011', '014', '015')),

    ('013', 'HBT2', 'Handboogtrainer 2', ('014', '015')),
    ('014', 'HBT3', 'Handboogtrainer 3', ('015',)),
    ('015', 'HBT4', 'Handboogtrainer 4', ()),

    ('017', 'HBI2', 'Handboog instructeur 2', ('018',)),
    ('018', 'HBI3', 'Handboog instructeur 3', ()),
    ('020', '', 'Basiscursus arbitrage', ()),

    ('030', 'WL2', 'Wedstrijdleider 25m1pijl', ('036',)),
    ('031', 'WL2', 'Wedstrijdleider Indoor/Outdoor', ('036',)),
    ('032', 'WL2', 'Wedstrijdleider 25m1pijl + Indoor', ('036',)),
    ('033', 'WL2', 'Wedstrijdleider Outdoor', ('036',)),
    ('034', 'WL2', 'Wedstrijdleider Indoor', ('036',)),
    ('035', 'WL2', 'Wedstrijdleider Allround (niveau 3)', ('036',)),
    ('036', 'WL1', 'Wedstrijdleider 1', ()),

    ('038', 'IFAA-RM', 'IFAA Range Marshall', ()),
    ('039', '', 'Praktijkbegeleider voor instructeurs', ()),

    ('040', 'SR3', 'Verenigingsscheidsrechter', ('041', '042')),
    ('041', 'SR4', 'Bondsscheidsrechter', ('042',)),
    ('042', 'SR5', 'Scheidsrechter internationaal', ()),
    ('043', '', 'Basisblok', ()),
    ('044', '', 'Scheidsrechter allround', ()),

    ('060', '', 'Autisme in de sport', ()),
    ('061', '', 'Preventie seksuele intimidatie', ()),
    ('062', '', 'Spec. aantekening aangepast sporten', ()),
    ('063', '', 'Workshop doping', ()),
    ('064', '', 'Experttraining arbitrage', ()),
    ('065', 'TTR', 'Spec. aantekening Traditioneel (HBT2)', ()),
    ('066', '', 'Basisschot bijscholing', ()),
    ('066a', '', 'Bewijs deelname Basisschot (geen cert)', ()),
    ('067', 'TTR', 'Certif. aantekening Traditioneel (HBT3)', ()),      # noqa
    ('068', '', 'Ianseo scoreverwerking', ()),
    ('069', '', 'Certificaat Basisschot', ()),      # pilot

    ('074', '', 'Sportief coachen', ()),

    ('080', 'PB', 'Praktijkbegeleider voor trainer/coach', ()),
    ('081', '', 'Mentor van cursisten Trainer A', ()),
    ('082', '', 'Leercoach', ()),
    ('083', '', 'Beoordelaar (portfolio/pvb)', ()),
    ('084', 'ON5', 'Opleider niveau 5 (docenten)', ()),
    ('084a', '', '(Bij-)scholing opl. opleiders-expert ASK', ()),

    ('085', 'TCO', 'Technical Control Officer (IFAA/DFBV)', ()),        # noqa
    ('086', '', 'Certificaat WA level 1 Coach', ()),
    ('087', '', 'Certificaat WA level 2 Coach', ()),
)

# logging to syslog
# zie https://docs.djangoproject.com/en/3.0/topics/logging/
# en  https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[django] %(asctime)s %(name)s [%(levelname)s] %(message)s",
            'datefmt': "%Y-%b-%d %H:%M:%S"
        }
    },
    'handlers': {
        'syslog': {
            # 'level': 'DEBUG',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'verbose',
            'facility': 'user',
            'address': '/dev/log'
        },
        # 'file': {
        #     'level': 'INFO',
        #     'class': 'logging.FileHandler',
        #     'filename': '/tmp/django.log'
        # },
    },
    'loggers': {
        'django': {
            'handlers': ['syslog'],
            'level': 'ERROR'            # Note: WARNING gives 1 log line for every code 404 (resource not found)
        },
        'xmlschema': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'asyncio': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'googlemaps': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'googleapiclient': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        '': {
            'handlers': ['syslog'],
            'level': 'INFO'
        }
    }
}

# speciale verenigingsnummer voor externe leden
# (let op: niet aanpassen)
EXTERN_VER_NR = 8000


# CRM import flexibiliteit
CRM_IMPORT_SKIP_MEMBERS = (101711,)            # CRM developer

CRM_IMPORT_GEEN_SECRETARIS_NODIG = (1377,)     # persoonlijk lid

CRM_IMPORT_GEEN_WEDSTRIJDEN = (1377,)          # persoonlijk lid, geen wedstrijden

CRM_IMPORT_GEEN_LOCATIE = (1368,               # bondsbureau
                           1377)               # persoonlijk lid, geen wedstrijden

# voorkom verwijderen bepaalde leden tijdens CRM import
CRM_IMPORT_BEHOUD_CLUB = (1999,                # voor demo
                          EXTERN_VER_NR)       # gast-accounts altijd behouden


# begin waarden voor unieke ticket nummers
# boekingsnummers: vanaf 1000000
TICKET_NUMMER_START__OPLEIDING = 3000000
TICKET_NUMMER_START__EVENEMENT = 6000000
TICKET_NUMMER_START__WEDSTRIJD = 7000000


# het verenigingsnummer van de bond
# wordt gebruikt als verenigingen via de bond betalingen mogen ontvangen
BETAAL_VIA_BOND_VER_NR = 1368

# welke vereniging(en) mogen een uitvoerende vereniging aanwijzen (en daar een locatie van kiezen)?
WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING = (1368,)

# welke verenigingen mogen de wedstrijdklassen ORGANISATIE_WA_STRIKT gebruiken?
WEDSTRIJDEN_WA_STRIKT_VER_NRS = (1368,)

IGNORE_CONTROLE_BEHEERDERS_VER_NRS = (EXTERN_VER_NR, 1368)


# aantal vragen van de instaptoets
INSTAPTOETS_AANTAL_VRAGEN = 20
INSTAPTOETS_AANTAL_GOED_EIS = 70        # procent
INSTAPTOETS_AANTAL_MINUTEN = 30

# google drive
GOOGLE_DRIVE_FOLDER_NAME_TOP = 'MH wedstrijdformulieren'        # moet uniek zijn in de drive
GOOGLE_DRIVE_FOLDER_NAME_TEMPLATES = 'MH templates RK/BK'       # moet uniek zijn in de drive
GOOGLE_DRIVE_FOLDER_SITE = NAAM_SITE

DDI_AUTH_TOKEN = ''     # your secret here

# -------------------------------------------
# defaults for 'dev' and 'test' options below
# -------------------------------------------

# SECURITY WARNING: don't run with debug turned on in production!
# let op: zonder DEBUG=True geen static files in dev omgeving!
DEBUG = False

# extensions are by default disabled
ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False

# minify html en javascript
ENABLE_MINIFY = True

# instrumentation of javascript
ENABLE_INSTRUMENT_JS = False

# HTML validation using v.Nu (see TestHelpers/e2ehelpers.py)        # noqa
TEST_VALIDATE_HTML = False

# JS validation using ESprima
TEST_VALIDATE_JAVASCRIPT = False

# use the complete font files or the subset files?
USE_SUBSET_FONT_FILES = True

# end of file
