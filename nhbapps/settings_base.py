# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
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
SITE_VERSIE = '2023-02-10'

# modules van de site
INSTALLED_APPS = [
    'Plein.apps.PleinConfig',           # must go first: provides admin template override
    'Beheer.apps.BeheerConfig',         # uitbreiding op admin interface
    'Account.apps.AccountConfig',
    'BasisTypen.apps.BasisTypenConfig',
    'Bestel.apps.BestelConfig',
    'Betaal.apps.BetaalConfig',
    'Bondspas.apps.BondspasConfig',
    'Competitie.apps.CompetitieConfig',
    'CompInschrijven.apps.CompInschrijvenConfig',
    'CompLaagBond.apps.CompLaagBondConfig',
    'CompLaagRegio.apps.CompLaagRegioConfig',
    'CompLaagRayon.apps.CompLaagRayonConfig',
    'CompBeheer.apps.CompBeheerConfig',
    'CompScores.apps.CompScoresConfig',
    'CompUitslagen.apps.CompUitslagenConfig',
    'Feedback.apps.FeedbackConfig',
    'Functie.apps.FunctieConfig',
    'HistComp.apps.HistCompConfig',
    'Kalender.apps.KalenderConfig',
    'Logboek.apps.LogboekConfig',
    'Mailer.apps.MailerConfig',
    'NhbStructuur.apps.NhbStructuurConfig',
    'Opleidingen.apps.OpleidingenConfig',
    'Overig.apps.OverigConfig',
    'Records.apps.RecordsConfig',
    'Score.apps.ScoreConfig',
    'Sporter.apps.SporterConfig',
    'Taken.apps.TakenConfig',
    'Vereniging.apps.VerenigingConfig',
    'Webwinkel.apps.WebwinkelConfig',
    'Wedstrijden.apps.WedstrijdenConfig',
    'django.contrib.staticfiles',   # gather static files from modules helper
    'django.contrib.sessions',      # support for database-backed sessions; needed for logged-in user
    'django.contrib.auth',          # authenticatie framework
    'django.contrib.contenttypes',  # permission association to models
    'django.contrib.messages',
]


# SecurityMiddleware
# SessionMiddleware
# AuthenticationMiddleware
# CommonMiddleware
# CsrfViewMiddleware: verifies POST belongs to GET
# MessageMiddleware: message storage between requests, typically for form feedback
# XFrameOptionsMiddleware

# AuthenticationMiddleware must be after SessionMiddleware
#        MessageMiddleware must be after SessionMiddleware

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

# sla alle datums in de database op als UTC
# dit doet PostgreSQL sowieso, onafhankelijk van deze instelling
# alleen vertalen bij presentatie naar de gebruiker toe
USE_TZ = True


# top-level URL verdeling naar apps
ROOT_URLCONF = 'nhbapps.urls'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'             # url
STATIC_ROOT = 'nhbapps/.static'     # relative to project top-dir
STATICFILES_DIRS = [
    os.path.join(PROJ_DIR, "compiled_static"),
    ("webwinkel_fotos", WEBWINKEL_FOTOS_DIR),
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
BACKGROUND_SYNC__BESTEL_MUTATIES = BACKGROUND_SYNC_POORT + 3
BACKGROUND_SYNC__BETAAL_MUTATIES = BACKGROUND_SYNC_POORT + 4

# our own test runner that executes the tests ordered by application hierarchy indicators to ensure that
# low-level errors are reported before applications depending that (broken) functionality report failures
TEST_RUNNER = 'nhbapps.app-hierarchy-testrunner.HierarchyRunner'

# applicatie specifieke settings
MINIMUM_LEEFTIJD_LID = 5

# minimum aantal scores in uitslag vorige seizoen nodig om te gebruiken als AG voor nieuwe seizoen
COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG = 6
COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG = 6
INTERLAND_25M_MINIMUM_SCORES_VOOR_DEELNAME = 6

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


# vertaling van discipline en beschrijving uit CRM naar volgorde (voor tonen op de site)
# volgorde: lager = beter
SPEELSTERKTE_VOLGORDE = (
    # discipline, beschrijving, volgorde
    ('NHB Graadspelden Schutter', 'Grootmeesterschutter', 1),       # 1e graad (3 van de 4)
    ('NHB Graadspelden Schutter', 'Meesterschutter', 2),            # 2e graad (3 van de 4)
    ('NHB Graadspelden Schutter', 'Allroundschutter', 3),           # 3e graad (4 van de 4)

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
    ('NHB Tussenspelden', '950',  203),

    # arrowhead
    ('Veld', 'Goud',   300),
    ('Veld', 'Zilver', 301),
    ('Veld', 'Wit',    302),
    ('Veld', 'Zwart',  303),
    ('Veld', 'Grijs',  304),
    ('Veld', 'Bruin',  305),
    ('Veld', 'Groen',  306),

    # ('Veld', 'Rode posten', 0),
    # ('Veld', 'Blauwe posten', 0),
    # ('Veld', 'Gele posten', 0),

    # Compound/Recurve
    ('World Archery Target Awards', 'Purper', 500),
    ('World Archery Target Awards', 'Goud',   501),
    ('World Archery Target Awards', 'Rood',   502),
    ('World Archery Target Awards', 'Blauw',  503),
    ('World Archery Target Awards', 'Zwart',  504),
    ('World Archery Target Awards', 'Wit',    505),

    # beginners awards
    ('Algemeen', 'Gouden Pijl', 600),
    ('Algemeen', 'Rode Pijl',   601),
    ('Algemeen', 'Blauwe Pijl', 602),
    ('Algemeen', 'Zwarte Pijl', 603),
    ('Algemeen', 'Witte Pijl',  604),
    ('Algemeen', 'Gouden Veer', 605),
    ('Algemeen', 'Rode Veer',   606),
)


OPLEIDING_CODES = (
    # code, afk-voor-pas, beschrijving, hogere-opleidingen
    ('011', 'HBT-A', 'Handboogtrainer A', ('014', '015')),
    ('012', 'HBT-B', 'Handboogtrainer B', ('011', '014', '015')),

    ('013', 'HBT2', 'Handboogtrainer 2', ('014', '015')),
    ('014', 'HBT3', 'Handboogtrainer 3', ('015',)),
    ('015', 'HBT4', 'Handboogtrainer 4', ()),

    ('017', 'HBI2', 'Handboog instructeur 2', ('018',)),
    ('018', 'HBI3', 'Handboog instructeur 3', ()),

    ('030', 'WL', 'Wedstrijdleider 25m1pijl', ()),
    ('031', 'WL', 'Wedstrijdleider Indoor/Outdoor', ()),
    ('032', 'WL', 'Wedstrijdleider 25m1pijl + Indoor', ()),
    ('033', 'WL', 'Wedstrijdleider Outdoor', ()),
    ('034', 'WL', 'Wedstrijdleider Indoor', ()),
    ('035', 'WL', 'Wedstrijdleider Allround (niveau 3)', ()),

    ('039', '', 'Praktijkbegeleider voor instructeurs', ()),

    ('040', 'SR3', 'Verenigingsscheidsrechter', ('041', '042')),
    ('041', 'SR4', 'Bondsscheidsrechter', ('042',)),
    ('042', 'SR5', 'Scheidsrechter internationaal', ()),

    ('043', '', 'Basisblok', ()),

    ('060', '', 'Autisme in de sport', ()),
    ('061', '', 'Preventie seksuele intimidatie', ()),
    ('062', '', 'Spec. aantekening aangepast sporten', ()),
    ('063', '', 'Workshop doping', ()),
    ('064', '', 'Experttraining arbitrage', ()),
    ('065', 'TTR', 'Spec. aantekening Traditioneel (HBT2)', ()),
    ('066', '', 'Basisschot bijscholing', ()),
    ('066a', '', 'Bewijs deelname Basisschot (geen cert)', ()),
    ('067', 'TTR', 'Certif. aantekening Traditioneel (HBT3)', ()),
    ('068', '', 'Ianseo scoreverwerking', ()),

    ('074', '', 'Sportief coachen', ()),

    ('080', 'PB', 'Praktijkbegeleider voor trainer/coach', ()),
    ('081', '', 'Mentor van cursisten Tr.A', ()),
    ('082', '', 'Leercoach', ()),
    ('083', '', 'Beoordelaar (portfolio/pvb)', ()),
    ('084a', '', '(Bij-)scholing opl. opleiders-expert ASK', ()),

    ('085', 'TCO', 'Technical Control Officer (IFAA/DFBV)', ()),
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

# CRM import flexibiliteit
CRM_IMPORT_SKIP_MEMBERS = (101711,)            # CRM developer

CRM_IMPORT_GEEN_SECRETARIS_NODIG = (1377,)     # persoonlijk lid

CRM_IMPORT_GEEN_WEDSTRIJDEN = (1377,)          # persoonlijk lid, geen wedstrijden

CRM_IMPORT_GEEN_WEDSTRIJDLOCATIE = (1368,      # bondsbureau NHB
                                    1377)      # persoonlijk lid, geen wedstrijden

CRM_IMPORT_BEHOUD_CLUB = (1999,)               # voor demo


# begin waarden voor unieke ticket nummers
# boekingsnummers: vanaf 1000000
TICKET_NUMMER_START__OPLEIDING = 3000000
TICKET_NUMMER_START__WEDSTRIJD = 7000000


# het verenigingsnummer van de NHB
# wordt gebruikt als verenigingen via de NHB betalingen mogen ontvangen
BETAAL_VIA_NHB_VER_NR = 1368

# implementation uses this instead of built-in default, to allow override during testing
BETAAL_API = 'https://api.mollie.com'


# welke vereniging(en) mogen een uitvoerende vereniging aanwijzen (en daar een locatie van kiezen)?
WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING = (1368,)


# defaults for 'dev' and 'test' options

# SECURITY WARNING: don't run with debug turned on in production!
# let op: zonder DEBUG=True geen static files in dev omgeving!
DEBUG = False

# HTML validation using v.Nu (see Overig/e2ehelpers.py)
TEST_VALIDATE_HTML = False

# end of file
