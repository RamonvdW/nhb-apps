# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
Django settings for the NhbApps project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# import install-specific settings from a separate file
# that is easy to replace as part of the deployment process
from nhbapps.settings_local import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJ_DIR)

# version of the site
# this is used to keep site feedback separated by version
SITE_VERSIE = '2022-03-20'

# modules van de site
INSTALLED_APPS = [
    'Plein.apps.PleinConfig',           # must go first: provides admin template override
    'Beheer.apps.BeheerConfig',         # uitbreiding op admin interface
    'Account.apps.AccountConfig',
    'BasisTypen.apps.BasisTypenConfig',
    'Bondspas.apps.BondspasConfig',
    'Competitie.apps.CompetitieConfig',
    'CompInschrijven.apps.CompInschrijvenConfig',
    'CompLaagRegio.apps.CompRegioConfig',
    'CompLaagRayon.apps.CompRayonConfig',
    'CompScores.apps.CompScoresConfig',
    'CompUitslagen.apps.CompUitslagenConfig',
    'Feedback.apps.FeedbackConfig',
    'Functie.apps.FunctieConfig',
    'Handleiding.apps.HandleidingConfig',
    'HistComp.apps.HistCompConfig',
    'Kalender.apps.KalenderConfig',
    'Logboek.apps.LogboekConfig',
    'Mailer.apps.MailerConfig',
    'NhbStructuur.apps.NhbStructuurConfig',
    'Overig.apps.OverigConfig',
    'Records.apps.RecordsConfig',
    'Score.apps.ScoreConfig',
    'Sporter.apps.SporterConfig',
    'Taken.apps.TakenConfig',
    'Vereniging.apps.VerenigingConfig',
    'Wedstrijden.apps.WedstrijdenConfig',
    'django.contrib.staticfiles',   # gather static files from modules helper
    'django.contrib.sessions',      # support for database-backed sessions; needed for logged-in user
    'django.contrib.auth',          # authenticatie framework
    'django.contrib.contenttypes',  # permission association to models
    'django.contrib.messages',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',                # security (https improvements)
    'django.contrib.sessions.middleware.SessionMiddleware',         # manage sessions across requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',                    # security (cross-site request forgery)
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',       # security
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',      # permission checking
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', ['nhbapps.minify_dtl.Loader']),
            ],
        },
    },
]


# point out location of WSGI application for django runserver command
WSGI_APPLICATION = 'nhbapps.wsgi.application'

# let browsers remember to connect with https
# security analysis recommends at least 180 days
SECURE_HSTS_SECONDS = 17280000      # 17280000 = 200 days


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
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


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'nl-NL'     # provides wanted date/time output format
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True

# format localization
USE_L10N = True

# sla alle datums in de database op als UTC
# dit doet PostgreSQL sowieso, onafhankelijk van deze instelling
# alleen vertalen bij presentatie naar de gebruiker toe
USE_TZ = True


# top-level URL verdeling naar apps
ROOT_URLCONF = 'nhbapps.urls'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'     # url
STATIC_ROOT = 'nhbapps/.static'     # relative to project top-dir
STATICFILES_DIRS = [
    os.path.join(PROJ_DIR, "compiled_static"),
]
STATICFILES_FINDER = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]


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
BACKGROUND_SYNC__REGIOCOMP_MUTATIES = BACKGROUND_SYNC_POORT + 1
BACKGROUND_SYNC__BONDSPAS_DOWNLOADER = BACKGROUND_SYNC_POORT + 2


# our own test runner that executes the tests ordered by application hierarchy indicators to ensure that
# low-level errors are reported before applications depending that (broken) functionality report failures
TEST_RUNNER = 'nhbapps.app-hierarchy-testrunner.HierarchyRunner'

# applicatie specifieke settings
MINIMUM_LEEFTIJD_LID = 5

# minimum aantal scores in uitslag vorige seizoen nodig om te gebruiken als AG voor nieuwe seizoen
COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG = 6
COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG = 6

# week waarin de laatste wedstrijden geschoten mogen worden
COMPETITIES_START_WEEK = 37
COMPETITIE_18M_LAATSTE_WEEK = 50        # week 37 t/m week 50
COMPETITIE_25M_LAATSTE_WEEK = 11        # week 37 t/m week 11

COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER = 4*7      # open 4 weeks after start week

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
    '90m',
    '70m',
    '60m',
    '50m',
    '50m (122cm)',
    '40m',
    '30m',
    '50m (72p)',
    '60m (72p)',
    '70m (72p)',
    '50m (15p)',
    '60m (12p)',
    '70m (12p)',

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


SPEELSTERKTE_VOLGORDE = (
    # discipline, beschrijving, volgorde
    ('NHB Graadspelden Schutter', 'Allroundschutter', 1),
    ('NHB Graadspelden Schutter', 'Meesterschutter', 2),
    ('NHB Graadspelden Schutter', 'Grootmeesterschutter', 3),

    ('NHB Graadspelden Indoor', '1e Graad Indoor', 10),
    ('NHB Graadspelden Indoor', '2e Graad Indoor', 11),
    ('NHB Graadspelden Indoor', '3e Graad Indoor', 12),

    ('NHB Graadspelden Outdoor', '1e Graad Outdoor', 20),
    ('NHB Graadspelden Outdoor', '2e Graad Outdoor', 21),
    ('NHB Graadspelden Outdoor', '3e Graad Outdoor', 22),

    ('NHB Graadspelden Veld', '1e Graad Veld', 30),
    ('NHB Graadspelden Veld', '2e Graad Veld', 31),
    ('NHB Graadspelden Veld', '3e Graad Veld', 32),

    ('NHB Graadspelden Short Metric', '1e Graad Short Metric', 40),
    ('NHB Graadspelden Short Metric', '2e Graad Short Metric', 41),
    ('NHB Graadspelden Short Metric', '3e Graad Short Metric', 42),

    ('Compound', 'Compound 1400', 100),
    ('Compound', 'Compound 1350', 101),
    ('Compound', 'Compound 1300', 102),
    ('Compound', 'Compound 1200', 103),
    ('Compound', 'Compound 1100', 104),
    ('Compound', 'Compound 1000', 105),

    ('Compound', 'Compound Cadet 1400', 110),
    ('Compound', 'Compound Cadet 1350', 111),
    ('Compound', 'Compound Cadet 1300', 112),
    ('Compound', 'Compound Cadet 1200', 113),
    ('Compound', 'Compound Cadet 1100', 114),
    ('Compound', 'Compound Cadet 1000', 115),

    ('Compound', 'Compound Master 1400', 120),
    ('Compound', 'Compound Master 1350', 121),
    ('Compound', 'Compound Master 1300', 122),
    ('Compound', 'Compound Master 1200', 123),
    ('Compound', 'Compound Master 1100', 124),
    ('Compound', 'Compound Master 1000', 125),

    ('Recurve', 'Recurve 1400', 130),
    ('Recurve', 'Recurve 1350', 131),
    ('Recurve', 'Recurve 1300', 132),
    ('Recurve', 'Recurve 1200', 133),
    ('Recurve', 'Recurve 1100', 134),
    ('Recurve', 'Recurve 1000', 135),

    ('Recurve', 'Recurve Cadet 1350', 141),
    ('Recurve', 'Recurve Cadet 1300', 142),
    ('Recurve', 'Recurve Cadet 1200', 143),
    ('Recurve', 'Recurve Cadet 1100', 144),
    ('Recurve', 'Recurve Cadet 1000', 145),

    ('Recurve', 'Recurve Master 1350', 151),
    ('Recurve', 'Recurve Master 1300', 152),
    ('Recurve', 'Recurve Master 1200', 153),
    ('Recurve', 'Recurve Master 1100', 154),
    ('Recurve', 'Recurve Master 1000', 155),

    # tussenspelden alleen op het RK in het eigen rayon
    ('NHB Tussenspelden', '1250', 200),
    ('NHB Tussenspelden', '1150', 201),
    ('NHB Tussenspelden', '1050', 202),
    ('NHB Tussenspelden', '950', 203),

    ('Veld', 'Goud', 301),
    ('Veld', 'Zilver', 302),
    ('Veld', 'Wit', 303),
    ('Veld', 'Zwart', 304),
    ('Veld', 'Grijs', 305),
    ('Veld', 'Bruin', 306),
    ('Veld', 'Groen', 307),

    ('Veld', 'Rode posten', 0),
    ('Veld', 'Blauwe posten', 0),
    ('Veld', 'Gele posten', 0),

    ('World Archery Target Awards', 'Purper', 0),
    ('World Archery Target Awards', 'Goud', 0),
    ('World Archery Target Awards', 'Rood', 0),
    ('World Archery Target Awards', 'Blauw', 0),
    ('World Archery Target Awards', 'Zwart', 0),
    ('World Archery Target Awards', 'Wit', 0),

    ('Algemeen', 'Blauwe Pijl', 0),
    ('Algemeen', 'Gouden Pijl', 0),
    ('Algemeen', 'Gouden Veer', 0),
    ('Algemeen', 'Rode Pijl', 0),
    ('Algemeen', 'Rode Veer', 0),
    ('Algemeen', 'Witte Pijl', 0),
    ('Algemeen', 'Zwarte Pijl', 0),
)


# pagina's van de handleiding
HANDLEIDING_TOP = 'Hoofdpagina'
HANDLEIDING_SEC = 'Handleiding_Secretaris'
HANDLEIDING_WL = 'Handleiding_Wedstrijdleider'
HANDLEIDING_HWL = 'Handleiding_Hoofdwedstrijdleider'
HANDLEIDING_RCL = 'Handleiding_RCL'
HANDLEIDING_PLANNING_REGIO = 'Planning_Regio'
HANDLEIDING_RKO = 'Handleiding_RKO'
HANDLEIDING_BKO = 'Handleiding_BKO'
HANDLEIDING_BB = 'Handleiding_BB'
HANDLEIDING_2FA = 'Twee-factor_authenticatie'
HANDLEIDING_ROLLEN = 'Rollen'
HANDLEIDING_INTRO_NIEUWE_BEHEERDERS = 'Intro_nieuwe_beheerders'
HANDLEIDING_SPORTERBOOG = 'Sporter-boog'
HANDLEIDING_INSCHRIJFMETHODES = 'Inschrijfmethodes_Regiocompetitie'
HANDLEIDING_CLUSTERS = 'Clusters'
HANDLEIDING_RK_SELECTIE = 'RK_selectie'
HANDLEIDING_RCL_INSTELLINGEN_REGIO = 'RCL_instellingen_regio'
HANDLEIDING_POULES = 'Poules'
HANDLEIDING_WEDSTRIJDKALENDER_HWL = 'Wedstrijdkalender_HWL'

HANDLEIDING_PAGINAS = [
    HANDLEIDING_TOP,
    HANDLEIDING_SEC,
    HANDLEIDING_WL,
    HANDLEIDING_HWL,
    HANDLEIDING_RCL,
    HANDLEIDING_RKO,
    HANDLEIDING_BKO,
    HANDLEIDING_BB,
    HANDLEIDING_2FA,
    HANDLEIDING_ROLLEN,
    HANDLEIDING_INTRO_NIEUWE_BEHEERDERS,
    HANDLEIDING_SPORTERBOOG,
    HANDLEIDING_PLANNING_REGIO,
    HANDLEIDING_INSCHRIJFMETHODES,
    HANDLEIDING_CLUSTERS,
    HANDLEIDING_RK_SELECTIE,
    HANDLEIDING_RCL_INSTELLINGEN_REGIO,
    HANDLEIDING_POULES,
    HANDLEIDING_WEDSTRIJDKALENDER_HWL,
    # pagina's van de handleiding die intern gerefereerd worden
    'Koppelen_beheerders'
]


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
        'saml2': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'djangosaml2idp': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'xmlschema': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'asyncio': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        '': {
            'handlers': ['syslog'],
            'level': 'INFO'
        }
    }
}

# defaults for 'dev' and 'test' options

# SECURITY WARNING: don't run with debug turned on in production!
# let op: zonder DEBUG=True geen static files in dev omgeving!
DEBUG = False

# HTML validation using v.Nu (see Overig/e2ehelpers.py)
TEST_VALIDATE_HTML = False

# end of file
