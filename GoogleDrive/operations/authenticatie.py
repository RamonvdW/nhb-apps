# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Krijg toestemming tot de Google Drive van een gebruiker """

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import AccessDeniedError, OAuth2Error
from GoogleDrive.models import Transactie, Token, maak_unieke_code

CLIENT_ID_AND_SECRET = settings.CREDENTIALS_PATH + 'mh_wedstrijdformulieren_oauth_client_id_and_secret.json'

SCOPES = ['https://www.googleapis.com/auth/drive']  # edit, create and delete all of your google drive files


def get_authorization_url(account_username: str, account_email: str):
    """ begin het process van toestemming krijgen tot de drive
        geeft een url terug waar de gebruiker heen gestuurd moet worden
    """
    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Aangevraagd door %s met e-mail %s\n" % (stamp_str, account_username, account_email)

    unieke_code = maak_unieke_code(when=stamp_str, username=account_username, email=account_email)
    transactie = Transactie.objects.create(unieke_code=unieke_code)

    # lees de json met de credentials
    flow = Flow.from_client_secrets_file(CLIENT_ID_AND_SECRET, scopes=SCOPES)

    # indicate where the API server will redirect the user after the user completes the authorization flow.
    # moet overeenkomen met een URI die opgezet is in Google console
    flow.redirect_uri = settings.SITE_URL + reverse('GoogleDrive:oauth-webhook')

    # handshake met Google om de URL te krijgen waar we de gebruiker heen moeten sturen
    authorization_url, state = flow.authorization_url(
                                        access_type='offline',              # recommended for web server
                                        #include_granted_scopes='true',     # optional; recommended
                                        #login_hint=account_email,          # laat keuze aan de gebruiker
                                        #prompt='consent',
                                        #prompt='select_account',
                                        state=transactie.unieke_code)

    msg += "[%s] authorization_url: %s\n" % (stamp_str, repr(authorization_url))
    transactie.log = msg
    transactie.save(update_fields=['log'])

    return authorization_url


def handle_authentication_response(webhook_uri):
    # lees de json met de credentials
    flow = Flow.from_client_secrets_file(CLIENT_ID_AND_SECRET, scopes=SCOPES)

    # indicate where the API server will redirect the user after the user completes the authorization flow.
    # moet overeenkomen met een URI die opgezet is in Google console
    flow.redirect_uri = settings.SITE_URL + reverse('GoogleDrive:oauth-webhook')

    try:
        host = settings.SITE_URL.replace('http://', 'https://')
        flow.fetch_token(authorization_response=host + webhook_uri)
    except (AccessDeniedError, OAuth2Error):
        # gebruiker heeft toestemming niet gegeven
        # of andere (algemene) fout
        # print('[ERROR] AccessDeniedError')
        token = None
    else:
        creds = flow.credentials
        if creds.valid and creds.refresh_token:
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Token ontvangen\n" % stamp_str
            token = Token.objects.create(creds=creds.to_json(),
                                         log=msg)
        else:
            # niet bruikbaar, want er zit geen refresh token bij
            # dit gebeurt als de gebruiker al eerder toestemming heeft gegeven en deze procedure nogmaals doorloopt
            token = None

    return token


def check_heeft_toestemming() -> bool:
    # geeft True terug als de gebruiker al toestemming gegeven heeft

    heeft_toestemming = False

    if Token.objects.exclude(has_failed=True).count() > 0:
        heeft_toestemming = True

    return heeft_toestemming


# end of file
