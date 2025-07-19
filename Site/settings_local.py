# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django local settings for the NhbApps project.

    This file is included from settings_base.py and contains specific
    settings that can be changed as part of a deployment, without
    having to edit the settings.py file.
"""

# NOTE: Site.core.setting_base has priority over this file (unable to override)

# the secret below ensures an adversary cannot fake aspects like a session-id
# just make sure it is unique per installation and keep it private
# details: https://docs.djangoproject.com/en/4.2/ref/settings/#secret-key
SECRET_KEY = '1234-replace-with-your-own-secret-key-56789abcdefg'       # noqa

# SITE_URL wordt gebruikt door TijdelijkeCodes, maar ook voor alle urls in e-mails
BASE_URL = "yourdomain.com"
#SITE_URL = "https://" + BASE_URL
SITE_URL = "http://localhost:8000"

ALLOWED_HOSTS = [
    'localhost',
]

IS_TEST_SERVER = True

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database-name',
        'USER': 'database-user',
        'PASSWORD': 'database-pwd',
        'HOST': 'localhost',
        'PORT': '5432'
    },
    'test': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database-name',
        'USER': 'database-user',
        'PASSWORD': 'database-pwd',
        'HOST': 'localhost',
        'PORT': '5432'
    },
}

# allow the database connections to stay open
CONN_MAX_AGE = None

# the issuer name that is sent to the OTP application in the QR code
OTP_ISSUER_NAME = "Your Site"

NAAM_SITE = "YourSite (dev)"

# begrens re-auth in dev omgeving
HERHAAL_INTERVAL_LOGIN = None
HERHAAL_INTERVAL_OTP = None

# aparte namen voor gebruik in e-mailafschrift bestelling
AFSCHRIFT_SITE_NAAM = "Your Site"
AFSCHRIFT_SITE_URL = "yourdomain.com"

# contactgegevens eerste- en tweedelijns support
EMAIL_BONDSBUREAU = "info@yourdomain.com"
EMAIL_SUPPORT = EMAIL_BONDSBUREAU
EMAIL_TECH_SUPPORT = "support@yourdomain.com"

# manuals (pdf)
URL_PDF_HANDLEIDING_LEDEN = 'https://yoursite/static/manual_members.pdf'
URL_PDF_HANDLEIDING_BEHEERDERS = 'https://yoursite/static/manual_managers.pdf'
URL_PDF_HANDLEIDING_VERENIGINGEN = 'https://yoursite/static/manual_clubs.pdf'
URL_PDF_HANDLEIDING_SCHEIDSRECHTERS = 'https://yoursite/static/manual_judges.pdf'

# sending e-mail via Postmark
#POSTMARK_URL = 'https://api.postmarkapp.com/email'
#POSTMARK_API_KEY = 'postmark private api key'
#EMAIL_FROM_ADDRESS = 'noreply@yourdomain.com'         # zie ook https://nl.wikipedia.org/wiki/Noreply

# e-mailadres om crashes te melden
EMAIL_DEVELOPER_TO = 'developer@yourdomain.com'
EMAIL_DEVELOPER_SUBJ = 'Internal Server Error: ' + NAAM_SITE

# wie mogen een mail krijgen?
#
# LET OP: registratie nieuw account gebruikt de whitelist niet!
#
# lege lijst --> mag naar iedereen mailen
EMAIL_ADDRESS_WHITELIST = ()

# url van het document privacyverklaring
PRIVACYVERKLARING_URL = 'url to privacy statement html, pdf or googledoc, etc'

# url van het document met voorwaarden voor A-status wedstrijden / alcoholbeleid
VOORWAARDEN_A_STATUS_URL = 'https://docs.google.com/document/d/random google document number/view'

# url van de documenten met de verkoopvoorwaarden
VERKOOPVOORWAARDEN_WEBWINKEL_URL = 'https://docs.google.com/document/d/yet another random google document number/pub'
VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL = 'https://docs.google.com/document/d/another random google document number/pub'
VERKOOPVOORWAARDEN_OPLEIDINGEN_URL = 'https://docs.google.com/document/d/yet another random google document number/pub'

# google doc id van het gsheet document
RECORDS_GSHEET_FILE_ID = 'random gsheet doc id'

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
INSTALL_PATH = '/directory/on/server/nhbapps-venv/project/'

# toon het kaartje Opleidingen?
TOON_OPLEIDINGEN = True

# bekende BIC codes, voor controle rekeninggegevens tijdens import uit CRM
BEKENDE_BIC_CODES = (
    'ABNANL2A',     # ABN AMRO bank                 # noqa
    'ASNBNL21',     # Volksbank / ASN bank          # noqa
    'INGBNL2A',     # ING bank                      # noqa
    'KNABNL2H',     # Knab (Aegon) --> ASR          # noqa
    'RABONL2U',     # Rabobank                      # noqa
    'RBRBNL21',     # Volksbank / Regiobank         # noqa
    'SNSBNL2A',     # SNS bank                      # noqa
    'TRIONL2U',     # Triodos bank                  # noqa
)

# na hoeveel dagen moet een product in het mandje automatisch vervallen?
# hierdoor komt een eventuele reservering weer beschikbaar voor iemand anders
MANDJE_VERVAL_NA_DAGEN = 3

# pagina over grensoverschrijdend gedrag en contactgegevens vertrouwenscontactpersonen
URL_VCP_CONTACTGEGEVENS = 'https://yourfrontend/contactgegevens-vcp/'   # noqa

# pagina met instructies en aanvraagformulier prestatiespelden
URL_SPELDEN_PROCEDURES = 'https://www.handboogsport.nl/de-khsn/#procedures'     # noqa

# online aanvraagformulier voor nieuwe records
URL_RECORD_AANVRAAGFORMULIER = 'https://docs.google.com/spreadsheets/1234_your_doc_7890'   # noqa

# landing page voor alle opleidingen
URL_OPLEIDINGEN = 'https://www.handboogsport.nl/opleidingen/'

# locatie op disk waar de foto's staan (bron)
# deze worden door collectstatic naar deployment gezet  # noqa
# het veld WebwinkelProduct.locatie is onder dit punt
WEBWINKEL_FOTOS_DIR = '/directory/on/server/webwinkel_fotos'    # noqa

# welke vereniging is de verkoper
WEBWINKEL_VERKOPER_VER_NR = 1368
WEBWINKEL_VERKOPER_BTW_NR = "012345678B99"

# verzendkosten webwinkel
WEBWINKEL_BRIEF_VERZENDKOSTEN_EURO = 4.25
WEBWINKEL_PAKKET_GROOT_VERZENDKOSTEN_EURO = 6.95

# ophalen op bondsbureau aan/uit zetten
WEBWINKEL_TRANSPORT_OPHALEN_MAG = True

# BTW percentage voor alle producten in de webwinkel, inclusief transportkosten
WEBWINKEL_BTW_PERCENTAGE = 21.0

# Prestatiespelden tonen in de webwinkel?
WEBWINKEL_TOON_PRESTATIESPELDEN = False

# welke vereniging(en) mogen evenementen op de kalender zetten?
# deze krijgen het kaartje Evenementen op het verenigingen overzicht
EVENEMENTEN_VERKOPER_VER_NRS = (1368,)

# welke vereniging(en) mogen opleidingen op de kalender zetten?
# deze krijgen het kaartje Opleidingen op het verenigingen overzicht
OPLEIDINGEN_VERKOPER_VER_NRS = (1368,)

# google maps URL (override) and API key
# (None = use library provided default)
GMAPS_API_URL = None  
GMAPS_KEY = 'AIzaDummy'

# voor sommige adressen werkt de geocode API niet...
# hier geven we het handmatige antwoord.
GEOCODE_FALLBACK = {
    "HEIDSEWEG 72A 5812AB HEIDE": (51.50199, 5.94793),              # noqa
    "HEIDSEWEG 72A 5812 AB HEIDE": (51.50199, 5.94793),             # noqa
    "HTTPS://GOO.GL/MAPS/5UHRTFEC4W7UAP2R7": (52.99786, 6.59954),   # noqa
}

# lidnummers van de scheidsrechters die geen mailtjes met beschikbaarheidsverzoeken willen ontvangen
LID_NRS_GEEN_SCHEIDS_BESCHIKBAARHEID_OPVRAGEN = ()

# Ledenvoordeel
TOON_LEDENVOORDEEL = False
WALIBI_URL_ALGEMEEN = 'https://www.walibi.nl/'
WALIBI_URL_KORTING = 'https://bit.ly/yourcode'

# toegestane tokens voor /kalender/api/lijst/30/?token=xxxx
KALENDER_API_TOKENS = ()

OVERIG_API_TOKENS = ()

# google doc id van het gsheet document
INSTAPTOETS_GSHEET_FILE_ID = 'another.google.sheets.id'     # noqa

# end of file
