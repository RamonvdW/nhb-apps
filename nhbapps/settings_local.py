# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
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
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
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

URL_PDF_HANDLEIDING_LEDEN = 'https://yourstite/static/manual_members.pdf'
URL_PDF_HANDLEIDING_BEHEERDERS = 'https://yoursite/static/manual_managers.pdf'
URL_PDF_HANDLEIDING_VERENIGINGEN = 'https://yoursitestatic/manual-clubs.pdf'


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

# url van de documenten met de verkoopvoorwaarden
VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL = 'https://docs.google.com/document/d/another random google document number/pub'
VERKOOPVOORWAARDEN_WEBWINKEL_URL = 'https://docs.google.com/document/d/yet another random google document number/pub'

# google doc id van het gsheet document
RECORDS_GSHEET_FILE_ID = 'random google document number'

# door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
RECORDS_GSHEET_SHEET_NAMES = [
    'Data individueel outdoor',
    'Data individueel indoor',
    'Data individueel 25m1pijl',
    'Data team'
]

# fonts die gebruikt worden om de bondspas text te tekenen
# deze moeten geïnstalleerd staan op het OS.
# gebruik fc-list en gnome-font-viewer
BONDSPAS_FONT = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
BONDSPAS_FONT_BOLD = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'

# the full path to the installation directory where each app subdirectory is located
# this is used to access resources like CompLaagRayon/files/template-excel-rk-teams.xls
INSTALL_PATH = '/directory/on/server/nhbapps-venv/nhb-apps/'

# toon het kaartje Opleidingen?
TOON_OPLEIDINGEN = True

# bekende BIC codes
BEKENDE_BIC_CODES = (
    'ABNANL2A',
    'FRBKNL2L',
    'INGBNL2A',
    'KNABNL2H',
    'RABONL2U',
    'RBRBNL21',
    'SNSBNL2A',
    'TRIONL2U'
)

# na hoeveel dagen moet een product in het mandje automatisch vervallen?
# hierdoor komt een eventuele reservering weer beschikbaar voor iemand anders
MANDJE_VERVAL_NA_DAGEN = 3

# pagina over grensoverschrijdend gedrag en contactgegevens VCP's
URL_VCP_CONTACTGEGEVENS = 'https://yourfrontend/grensoverschrijdend-gedrag/'

# locatie op disk waar de foto's staan (bron)
# deze worden door collectstatic naar deployment gezet
# het veld WebwinkelProduct.locatie is onder dit punt
WEBWINKEL_FOTOS_DIR = '/directory/on/server/webwinkel_fotos'

# welke vereniging is de verkoper
WEBWINKEL_VERKOPER_VER_NR = 1368

# verzendkosten voor een pakketje tot 10kg via PostNL
WEBWINKEL_PAKKET_VERZENDKOSTEN_EURO = 6.75      # 6.95 vanaf 1 jan 2023

# verzendkosten briefpost tot 350g via PostNL
WEBWINKEL_BRIEF_VERZENDKOSTEN_EURO = 4.04       # 4.15 vanaf 1 jan 2023

# end of file
