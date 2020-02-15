# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
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

# NOTE: some setting have been moved to settings_local.py
#       see end of this file

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJ_DIR)

# version of the site
# this is used to keep site feedback separated to version
SITE_VERSIE = 'test 2020-02-15'

# modules van de site
INSTALLED_APPS = [
    'Plein.apps.PleinConfig',
    'Beheer.apps.BeheerConfig',
    'NhbStructuur.apps.NhbStructuurConfig',
    'Account.apps.AccountConfig',
    'BasisTypen.apps.BasisTypenConfig',
    'Competitie.apps.CompetitieConfig',
    'HistComp.apps.HistCompConfig',
    'Records.apps.RecordsConfig',
    'Overig.apps.OverigConfig',
    'Logboek.apps.LogboekConfig',
    'Mailer.apps.MailerConfig',
    'djangosaml2idp',               # single sign-on Identity Provider (IP) using SAML2 (Security Assertion Markup Language)
    'django.contrib.staticfiles',   # gather static files from modules helper
    'django.contrib.sessions',      # support for database-backed sessions; needed for logged-in user
    'django.contrib.admin',         # see-all/fix-all admin pages
    'django.contrib.auth',          # authenticatie framework
    'django.contrib.contenttypes',  # permission association to models
    'django.contrib.messages',
    #'debug_toolbar',                # DEV ONLY
    #'django_extensions'             # DEV ONLY
]


MIDDLEWARE = [
    #'debug_toolbar.middleware.DebugToolbarMiddleware',          # DEV ONLY
    'django.middleware.security.SecurityMiddleware',                # security (https improvements)
    'django.contrib.sessions.middleware.SessionMiddleware',         # manage sessions across requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',                    # security (cross-site scripting)
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


# vervanger van (aanpassing/uitbreiding op)  de ingebouwde User
AUTH_USER_MODEL = 'Account.Account'

# maximum aantal keer dat een verkeerd wachtwoord opgegeven mag worden
# voor een account (login of wijzig-wachtwoord) voor het geblokkeerd wordt
AUTH_BAD_PASSWORD_LIMIT = 5
AUTH_BAD_PASSWORD_LOCKOUT_MINS = 15


# templates (django template language) processors
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #'DIRS': [ str(APPS_DIR.path('templates')), ],
        #'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',      # permission checking
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'nhb-apps.minify_dtl.Loader',
                    ]
                ),
            ],
        },
    },
]


# point out location of WSGI application for django runserver command
WSGI_APPLICATION = 'nhb-apps.wsgi.application'

# let browsers remember to connect with https
SECURE_HSTS_SECONDS = 8640000      # 8640000 = 100 days


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
#LANGUAGE_CODE = 'en-us'
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
    os.path.join(PROJ_DIR, "global_static"),
]
STATICFILES_FINDER = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]


# wordt gebruikt door LoginView als er geen 'next' veld bij de POST zit
#LOGIN_REDIRECT_URL = '/plein/'

# wordt gebruikt door de permission_required decorator en UserPassesTextMixin
# om de gebruiker door te sturen als een view geen toegang verleend
LOGIN_URL = '/account/login/'


# for debug_toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]


# applicatie specifieke settings
MINIMUM_LEEFTIJD_LID = 5

# maximum aantal resultaten dat een doorzoeking van de records terug geeft
# dit voorkomt honderden resultaten bij het zoeken naar de letter e
# 150 omdat bepaalde plaatsen veel records hebben, zoals Schijndel (93 in Okt 2019)
RECORDS_MAX_ZOEKRESULTATEN = 150

# de mogelijke waarden voor soort_record in de administratie van de NL records
# wordt gebruikt om invoerfouten te ontdekken en rapporteren
RECORDS_TOEGESTANE_SOORTEN = (

    # outdoor
    '30m',
    '40m',
    '50m',
    '50m (15p)',
    '50m (122cm)',
    '50m (72p)',
    '60m',
    '60m (12p)',
    '60m (72p)',
    '70m',
    '70m (12p)',
    '70m (72p)',
    '90m',
    'WA1440',
    '288p',

    # Outdoor, still to be cleaned up
    'Fita RK Rayon 4',
    'ShortMetric',

    # indoor
    '18m (15p)',
    '18m (60p)',
    '18m',
    '18m (12p)',
    '25m',
    '25m (60p)',
    '25m+18m (60p)',
    '25m+18m (120p)',

    # Indoor, to be cleaned up
    'match (15p)',

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
)

# import install-specific settings from a separate file
# that is easy to replace as part of the deployment process
from .settings_local import *

# definitions taken from saml2.saml to avoid importing saml2
# because it replaces ElementTree with cElementTree, which gives problems with QR code generation
NAMEID_FORMAT_UNSPECIFIED = 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified'
NAMEID_FORMAT_EMAILADDRESS = 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
BINDING_HTTP_REDIRECT = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
BINDING_HTTP_POST = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'

SAML_BASE_URL = BASE_URL + '/idp'

SAML_IDP_CONFIG = {
     'debug' : DEBUG,
     'xmlsec_binary': '/usr/bin/xmlsec1',

     # the SAML entity id of this side, the Identity Provider
     # just a globally unique string
     'entityid': 'NHB IT applications SAML2 Identity Provider',

     # metadata for trusted service providers (like mediawiki)
     'metadata': { 'local': os.path.join(PROJ_DIR, 'saml2_sp_metadata.xml') },      # same dir as this file
     #'metadata': { 'local': os.path.join(BASE_DIR, 'data_private/saml2/saml2_sp_metadata.xml') },

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
             'name_id_format': [NAMEID_FORMAT_EMAILADDRESS, NAMEID_FORMAT_UNSPECIFIED],
             'sign_response': False,         # TODO: set to True?
             'sign_assertion': False,        # TODO: set to True?
             # signing
             'key_file': os.path.join(PROJ_DIR, 'data_private/saml2/private.key'),
             'key_file': os.path.join(PROJ_DIR, 'data_private/saml2/cert.crt'),
             'valid_for': 100*24,
         }
     }
}

SAML_IDP_SPCONFIG = {
     # configuration of trusted service providers
     # entry name = entity_id
     'https://wiki.handboogsport.st-visir.nl/saml/module.php/saml/sp/metadata.php/default-sp': {
         'processor': 'djangosaml2idp.processors.BaseProcessor',
         'nameid_field': 'staffID',
         'sign_response': False,
         'sign_assertion': False,
         'attribute_mapping': {
             # Account.fieldname --> expose how
             'first_name': 'real_name',
             'username': 'username',
             'email': 'email'
         }
     },
}

# end of file
