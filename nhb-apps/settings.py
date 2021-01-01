# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
Django settings for the nhb-apps project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys

# import install-specific settings from a separate file
# that is easy to replace as part of the deployment process
from .settings_local import *

# for testing
# TODO: dit werkt niet: ./manage.py --enable-wiki runserver
# TODO: dit werkt niet: ./manage.py runserver -- --enable-wiki  --> deze file wordt 2x ingeladen
if "--enable-wiki" in sys.argv:
    ENABLE_WIKI = True
    sys.argv.remove("--enable-wiki")

# enable html validation using v.Nu (warning: triples test duration)
TEST_VALIDATE_HTML = False

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJ_DIR)

# version of the site
# this is used to keep site feedback separated by version
SITE_VERSIE = '2021-01-01'

# modules van de site
INSTALLED_APPS = [
    'Plein.apps.PleinConfig',
    'Beheer.apps.BeheerConfig',             # replaces admin
    'NhbStructuur.apps.NhbStructuurConfig',
    'Account.apps.AccountConfig',
    'BasisTypen.apps.BasisTypenConfig',
    'Functie.apps.FunctieConfig',
    'Competitie.apps.CompetitieConfig',
    'HistComp.apps.HistCompConfig',
    'Records.apps.RecordsConfig',
    'Overig.apps.OverigConfig',
    'Logboek.apps.LogboekConfig',
    'Mailer.apps.MailerConfig',
    'Vereniging.apps.VerenigingConfig',
    'Schutter.apps.SchutterConfig',
    'Score.apps.ScoreConfig',
    'Taken.apps.TakenConfig',
    'Wedstrijden.apps.WedstrijdenConfig',
    'Handleiding.apps.HandleidingConfig',
    'django.contrib.staticfiles',   # gather static files from modules helper
    'django.contrib.sessions',      # support for database-backed sessions; needed for logged-in user
    'django.contrib.admin',         # see-all/fix-all admin pages
    'django.contrib.auth',          # authenticatie framework
    'django.contrib.contenttypes',  # permission association to models
    'django.contrib.messages',
    # 'django_extensions'             # very useful for show_urls
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

if ENABLE_WIKI:
    # single sign-on Identity Provider (IP)
    #   using SAML2 (Security Assertion Markup Language)
    INSTALLED_APPS.append('djangosaml2idp')

if ENABLE_DEBUG_TOOLBAR and "test" not in sys.argv:    # pragma: no cover
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

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
                ('django.template.loaders.cached.Loader', ['nhb-apps.minify_dtl.Loader']),
            ],
        },
    },
]


# point out location of WSGI application for django runserver command
WSGI_APPLICATION = 'nhb-apps.wsgi.application'

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
ROOT_URLCONF = 'nhb-apps.urls'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'     # url
STATIC_ROOT = 'nhb-apps/.static'     # relative to project top-dir
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


BACKGROUND_SYNC_POORT = 3000
BACKGROUND_SYNC__KAMPIOENSCHAP_MUTATIES = BACKGROUND_SYNC_POORT + 1


# our own test runner that executes the tests ordered by application hierarchy indicators to ensure that
# low-level errors are reported before applications depending that (broken) functionality report failures
TEST_RUNNER = 'nhb-apps.app-hierarchy-testrunner.HierarchyRunner'

# applicatie specifieke settings
MINIMUM_LEEFTIJD_LID = 5

# minimum aantal scores in uitslag vorige seizoen nodig om te gebruiken als AG voor nieuwe seizoen
COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG = 6
COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG = 5   # uitzondering voor 2020/2021 in verband met corona

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

    # Outdoor, TODO: still to be cleaned up
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


RECORDS_TOEGESTANE_PARA_KLASSEN = (
    "Open",
    "Staand",
    "W1",
    "W2",
    "Ja"        # aka Onbekend
    # TODO: hier ontbreken VI1 en VI2/3
)

# definitions taken from saml2.saml to avoid importing saml2
# because it replaces ElementTree with cElementTree, which gives problems with QR code generation
NAMEID_FORMAT_UNSPECIFIED = 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified'
# NAMEID_FORMAT_EMAILADDRESS = 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
BINDING_HTTP_REDIRECT = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
BINDING_HTTP_POST = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'

SAML_BASE_URL = SITE_URL + '/idp'

SAML_IDP_CONFIG = {
    'debug': DEBUG,
    'xmlsec_binary': '/usr/bin/xmlsec1',

    # the SAML entity id of this side, the Identity Provider
    # just a globally unique string
    'entityid': 'NHB IT applications SAML2 Identity Provider',

    # our service description (the identity provider)
    'service': {
         'idp': {
             'name': 'NHB IT applications IdP',
             'endpoints': {
                 'single_sign_on_service': [
                     (SAML_BASE_URL + '/sso/post',     BINDING_HTTP_POST),
                     (SAML_BASE_URL + '/sso/redirect', BINDING_HTTP_REDIRECT)
                 ]
             },
             'name_id_format': [NAMEID_FORMAT_UNSPECIFIED],
             # signing assertion and responses is mandatory in SAML 2.0
             'sign_response': True,
             'sign_assertion': True
         }
    },

    # signing keys
    'key_file': os.path.join(BASE_DIR, 'data_private/saml2/private.key'),
    'cert_file': os.path.join(BASE_DIR, 'data_private/saml2/cert.crt'),
    'valid_for': 100*24
}

# SP to be entered into the database using admin interface
# details:
#   EntityId  https://wiki.handboogsport.st-visir.nl/saml/module.php/saml/sp/metadata.php/default-sp
#   processor Functie.idp_accesscheck.WikiAccessCheck
#   Attribute-mapping (JSON)
#       (Account.field_name: expose as)
#       (Account.method_name: expose as)
"""
{
"username": "username",
"get_email": "emailAddress",
"volledige_naam": "real_name"
}
"""

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
HANDLEIDING_SCHUTTERBOOG = 'Schutter-boog'
HANDLEIDING_INSCHRIJFMETHODES = 'Inschrijfmethodes_Regiocompetitie'
HANDLEIDING_CLUSTERS = 'Clusters'
HANDLEIDING_RK_SELECTIE = 'RK_selectie'

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
    HANDLEIDING_SCHUTTERBOOG,
    HANDLEIDING_PLANNING_REGIO,
    HANDLEIDING_INSCHRIJFMETHODES,
    HANDLEIDING_CLUSTERS,
    HANDLEIDING_RK_SELECTIE,
    # pagina's van de handleiding die intern gerefereerd worden
    'Tips_voor_wiki_gebruik',
    'Handleiding_CWZ',
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
            'level': 'DEBUG',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'verbose',
            'facility': 'user',
            'address': '/dev/log'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['syslog'],
            'level': 'ERROR'
        },
        'saml2': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        'djangosaml2idp': {
            'handlers': ['syslog'],
            'level': 'WARNING'
        },
        '': {
            'handlers': ['syslog'],
            'level': 'DEBUG'
        }
    }
}

# end of file
