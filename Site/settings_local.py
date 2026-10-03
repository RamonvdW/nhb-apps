# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
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
# details: https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key
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
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
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
EMAIL_TECH_SUPPORT = 'support@yourdomain.com'

SITE_STATIC_PDFS = SITE_URL + '/mh-static/pdfs/'

# handleidingen
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

# waar staat het text document privacyverklaring?
PRIVACYVERKLARING_FILE = '/directory/on/server/nhbapps-venv/project/privacyverklaring.txt'   # noqa

# url van het document met voorwaarden voor A-status wedstrijden / alcoholbeleid
VOORWAARDEN_A_STATUS_URL = SITE_STATIC_PDFS + 'voorwaarden-a-status-wedstrijd.pdf'

# url van de documenten met de verkoopvoorwaarden
VERKOOPVOORWAARDEN_WEBWINKEL_URL   = SITE_STATIC_PDFS + 'verkoopvoorwaarden-webwinkel.pdf'
VERKOOPVOORWAARDEN_EVENEMENTEN_URL = SITE_STATIC_PDFS + 'verkoopvoorwaarden-evenementen.pdf'
VERKOOPVOORWAARDEN_OPLEIDINGEN_URL = SITE_STATIC_PDFS + 'verkoopvoorwaarden-opleidingen.pdf'

# fonts die gebruikt worden om de bondspas text te tekenen
# deze moeten geïnstalleerd staan op het OS.
# gebruik fc-list en gnome-font-viewer
BONDSPAS_FONT = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
BONDSPAS_FONT_BOLD = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'

# the full path to the installation directory where each app subdirectory is located
# this is used to access resources like CompKampioenschap/files/template-excel-teams.xlsx
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
URL_PROCEDURES = 'https://your.site/relevant/url/'     # noqa

# online aanvraagformulier voor nieuwe records
URL_RECORD_AANVRAAGFORMULIER = 'https://docs.google.com/spreadsheets/1234_your_doc_7890'   # noqa

# landing page voor alle opleidingen
URL_OPLEIDINGEN = 'https://your.site/relevant/url/'

# let op: zonder / aan het einde, want die geeft een redirect (302) en dat rapporteert de href checker
URL_FOTOBANK_INDOOR = 'https://your.site/photos/Indoor'

# locatie op disk waar de foto's staan (bron)
# deze worden door collectstatic naar deployment gezet  # noqa
# het veld WebwinkelProduct.locatie is onder dit punt
WEBWINKEL_FOTOS_DIR = '/directory/on/server/webwinkel_fotos'    # noqa
STATIC_PDFS_DIR = '/directory/on/server/static_pdfs'

# welke vereniging is de verkoper
WEBWINKEL_VERKOPER_VER_NR = 1368
WEBWINKEL_VERKOPER_BTW_NR = "012345678B99"

# verzendkosten webwinkel

# envelop (maat t/m C4 (kan A4 in), gewicht t/m 20 gram) exclusief kosten envelop en afhandeling
WEBWINKEL_ENVELOP_VERZENDKOSTEN_EURO = 1.40

# klein = brievenbus-pakje (max 380x265x32mm, max 2kg) exclusief kosten doosje en afhandeling
WEBWINKEL_PAKKET_2KG_VERZENDKOSTEN_EURO = 4.55

# groot = bezorging op huisadres (max 1000x500x500mm, max 10kg), exclusief kosten doosje en afhandeling
WEBWINKEL_PAKKET_10KG_VERZENDKOSTEN_EURO = 7.45

# ophalen op bondsbureau aan/uit zetten
WEBWINKEL_TRANSPORT_OPHALEN_MAG = True

# BTW percentage voor alle producten in de webwinkel, inclusief transportkosten
WEBWINKEL_BTW_PERCENTAGE = 21.0

# Prestatiespelden tonen in de webwinkel?
TOON_SPELDEN_BESTELLEN = False

# welke vereniging(en) mogen evenementen op de kalender zetten?
# deze krijgen het kaartje Evenementen op het verenigingen overzicht
EVENEMENTEN_VERKOPER_VER_NRS = (1368,)

# welke vereniging(en) mogen opleidingen op de kalender zetten?
# deze krijgen het kaartje Opleidingen op het verenigingen overzicht
OPLEIDINGEN_VERKOPER_VER_NRS = (1368,)

# google maps URL (override) and API key
# (None = use library provided default)
GOOGLEMAPS_API_URL = None  
GOOGLEMAPS_API_KEY = 'AIzaDummy'

# hoe vaak de reistijd verversen?
# 183 dagen = 6 maanden
REISTIJD_VERVERSEN_NA_DAGEN = 183

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

INSTAPTOETS_LESMATERIAAL_WA_BOEKEN = 'url'
INSTAPTOETS_LESMATERIAAL_COMPETITIE = 'url'
INSTAPTOETS_LESMATERIAAL_KLEDINGVOORSCHRIFT = 'url'

# met wie de wedstrijdformulieren folder delen?
GOOGLE_DRIVE_SHARE_WITH = []
GOOGLE_DRIVE_FOLDER_SITE = 'Subdir name'

# waar staan de json bestanden voor de service accounts etc.
# wordt gebruikt door diverse diensten: downloaders records/instaptoets, backup uploader, google drive toegang, etc.
# filenames zijn bekend bij deze diensten
CREDENTIALS_PATH = '/directory/on/your/server/'

# client id en secret voor toegang tot de Google Drive van een gebruiker
CREDENTIALS_OAUTH_GOOGLE_DRIVE = 'file_with_credentials.json'

# wedstrijdenformulieren zijn gedeeld met dit service account, voor updaten en importeren
CREDENTIALS_SERVICE_ACCOUNT_WEDSTRIJDFORMULIEREN = 'file1_with_credentials_service-account.json'

# link naar het CRM systeem
CRM_URL = 'url'
CRM_TITEL = 'title'
CRM_BESCHRIJVING = 'Persoonsgegevens van leden worden geadministreerd in een apart systeem.'


# voeg /_api/site/id/ toe om aan de site url (vereist dat je ingelogd bent en toegang hebt)
# retourneert een kort xml doc met het site id:

# credentials voor toegang to shared document op Sharepoint/Teams site van de bond
GRAPH_IDS = {
    'tenant_id': 'b9999999-8888-7777-6666-543210123456',        # company

    # for each site, add a numerical index
    # these numbers can be used from the management commands graph_*, parameter site_index

    # https://yoursite.sharepoint.com/sites/Folder-Name/_api/site/id/
    # <d:Id m:type="Edm.Guid">12345678-1234-1234-1234-123456789abc</d:Id>
    1: {
        'description': 'YourSite-Docs',
        'site_id': '12345678-1234-1234-1234-123456789abc',
        'client_id: 'b8888888-9999-4444-6666-543210123456',
        'client_secret': 'sssst',
    },
}

# token required to access the DataApi
DDI_AUTH_TOKEN="your Secret Here"

# end of file
