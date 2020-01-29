# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
Django local settings for the nhb-apps project.

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

SITE_URL = "https://yourdomain.com"         # used by Overige:tijdelijke urls

ALLOWED_HOSTS = [
    '127.0.0.1'
]

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
OTP_ISSUER_NAME = "yoursite.com"

# sending email via MailGun
MAILGUN_URL = 'https://api.eu.mailgun.net/v3/yourdomain.com/messages'
MAILGUN_API_KEY = 'mailgun private api key'
EMAIL_FROM_ADDRESS = 'noreply@yourdomain.com'         # zie ook https://nl.wikipedia.org/wiki/Noreply

# google doc id van het gsheet document
RECORDS_GSHEET_FILE_ID = 'random google document number'

# door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
RECORDS_GSHEET_SHEET_NAMES = [
    'Data individueel outdoor',
    'Data individueel indoor',
    'Data individueel 25m1pijl',
    'Data team'
]

# url van de wiki server
WIKI_URL = 'http://wiki.yourdomain.com'

# end of file

