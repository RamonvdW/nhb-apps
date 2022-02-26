# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django local settings for the NhbApps project.

    This file is included from settings_base.py and contains specific
    settings that can be changed as part of a deployment, without
    having to edit the settings.py file.
"""

# the secret below ensures an adversary cannot fake aspects like a session-id
# just make sure it is unique per installation and keep it private
# details: https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key
SECRET_KEY = '1234-replace-with-your-own-secret-key-56789abcdefg'

BASE_URL = "yourdomain.com"

# SITE_URL wordt gebruikt door Overige:tijdelijke urls
#SITE_URL = "https://" + BASE_URL
SITE_URL = "http://localhost:8000"

ALLOWED_HOSTS = ['localhost']

IS_TEST_SERVER = True

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
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

# allow the database connections to stay open
CONN_MAX_AGE = None

# the issuer name that is sent to the OTP application in the QR code
OTP_ISSUER_NAME = "yourdomain.com"

NAAM_SITE = "YourSite (dev)"

EMAIL_BONDSBUREAU = "info@handboogsport.nl"
EMAIL_SUPPORT = EMAIL_BONDSBUREAU


# sending e-mail via Postmark
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


# bondspassen ophalen bij OnzeRelaties en lokaal cachen
#BONDSPAS_CACHE_PATH = '/var/spool/bondspas-cache/'
BONDSPAS_CACHE_PATH = '/tmp/'
BONDSPAS_MAX_SIZE_MB = 100          # 150kB/stuk --> genoeg voor 682 passen
BONDSPAS_MAX_SIZE_PDF_KB = 500      # accepteer een pdf alleen al deze minder is dan 500kB
BONDSPAS_RETRY_MINUTES = 5          # 5 minuten wachten, dan pas opnieuw proberen
#BONDSPAS_DOWNLOAD_URL = 'download-url'  # bondsnummer
BONDSPAS_DOWNLOAD_URL = 'http://localhost:8124/bondspas/%s'   # bondsnummer


# voor wie een taak aanmaken over feedback?
TAAK_OVER_FEEDBACK_ACCOUNTS = [
    # comma-separated list of account usernames
]

# the full path to the installation directory where each app subdirectory is located
# this is used to access resources like CompRayon/files/template-excel-rk-teams.xls
INSTALL_PATH = '/var/www/nhb-apps-venv/nhb-apps/'


# end of file
