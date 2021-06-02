# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django local settings for the NhbApps project.

    This file is included from settings.py and contains specific
    settings that can be changed as part of a deployment, without
    having to edit the settings.py file.
"""

# the secret below ensures an adversary cannot fake aspects like a session-id
# just make sure it is unique per installation and keep it private
# details: https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key
SECRET_KEY = '1234-replace-with-your-own-secret-key-56789abcdefg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ENABLE_DEBUG_TOOLBAR = False

SITE_URL = "https://yourdomain.com"         # used by Overige:tijdelijke urls and SAML2

ALLOWED_HOSTS = [
    '127.0.0.1'
]

IS_TEST_SERVER = False

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database-name',
        'USER': 'database-user',
        'PASSWORD': 'database-pwd',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# the issuer name that is sent to the OTP application in the QR code
OTP_ISSUER_NAME = "yourdomain.com"

NAAM_SITE = "YourSite (dev)"

EMAIL_BONDSBURO = "info@handboogsport.nl"

# sending email
#POSTMARK_URL = 'https://api.postmarkapp.com/email'
#POSTMARK_API_KEY = 'postmark private api key'
#EMAIL_FROM_ADDRESS = 'noreply@yourdomain.com'         # zie ook https://nl.wikipedia.org/wiki/Noreply

EMAIL_DEVELOPER_TO = 'developer@yourdomain.com'
EMAIL_DEVELOPER_SUBJ = 'Internal Server Error: ' + NAAM_SITE


# users allowed to send to in this test setup
# if empty, allows sending to anybody
EMAIL_ADDRESS_WHITELIST = ()


# url van het document privacyverklaring
PRIVACYVERKLARING_URL = 'url to privacy statement html, pdf or googledoc, etc'

# url van het document met voorwaarden voor A-status wedstrijden
VOORWAARDEN_A_STATUS_URL = 'https://docs.google.com/document/d/random google document number/view'

# google doc id van het gsheet document
RECORDS_GSHEET_FILE_ID = 'random google document number'

# door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
RECORDS_GSHEET_SHEET_NAMES = [
    'Data individueel outdoor',
    'Data individueel indoor',
    'Data individueel 25m1pijl',
    'Data team'
]


# use static manual pages (wiki is for the test server only)
ENABLE_WIKI = False
# ondersteuning van de Wiki met SSO via de IdP, of ingebouwde handleiding?
WIKI_URL = 'http://wiki.yourdomain.com'

# vertaling van tijdelijke (99xxxx nummers) naar correcte NHB nummer
MAP_99_NRS = {
    990001: 1234567,
}

# end of file
