# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Krijg toestemming tot de Google Drive van een gebruiker """

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import AccessDeniedError, OAuth2Error
from GoogleDrive.models import Transactie, Token, maak_unieke_code
import logging
import os.path

CLIENT_ID_AND_SECRET = os.path.join(settings.CREDENTIALS_PATH,
                                    settings.CREDENTIALS_OAUTH_GOOGLE_DRIVE)

SCOPES = ['https://www.googleapis.com/auth/drive']  # edit, create and delete all of your google drive files

my_logger = logging.getLogger('MH.GoogleDrive')


def get_authorization_url(account_username: str, account_email: str):
    """ begin het process van toestemming krijgen tot de drive
        geeft een url terug waar de gebruiker heen gestuurd moet worden
    """
    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Aangevraagd door %s met e-mail %s\n" % (stamp_str, account_username, account_email)

    unieke_code = maak_unieke_code(when=stamp_str, username=account_username, email=account_email)
    transactie = Transactie.objects.create(unieke_code=unieke_code)

    # indicate where the API server will redirect the user after the user completes the authorization flow.
    # moet overeenkomen met een URI die opgezet is in Google console
    redirect_uri = settings.SITE_URL + reverse('GoogleDrive:oauth-webhook')

    # lees de json met de credentials
    flow = Flow.from_client_secrets_file(
                            CLIENT_ID_AND_SECRET,
                            scopes=SCOPES,
                            redirect_uri=redirect_uri)

    # handshake met Google om de URL te krijgen waar we de gebruiker heen moeten sturen
    authorization_url, state = flow.authorization_url(
                                        access_type='offline',              # recommended for web server
                                        #include_granted_scopes='true',     # optional; recommended
                                        #login_hint=account_email,          # laat keuze aan de gebruiker
                                        #prompt='consent',
                                        #prompt='select_account',
                                        state=transactie.unieke_code)

    my_logger.info("{handle_authentication_response} unieke_code=%s, state=%s" % (repr(unieke_code), repr(state)))
    my_logger.info("{handle_authentication_response} flow.code_verifier=%s" % repr(flow.code_verifier))

    transactie.code_verifier = flow.code_verifier

    msg += "[%s] authorization_url: %s\n" % (stamp_str, repr(authorization_url))
    transactie.log = msg

    transactie.save(update_fields=['log', 'code_verifier'])

    return authorization_url


def handle_authentication_response(webhook_uri, transactie: Transactie):
    my_logger.info("{handle_authentication_response} webhook_uri=%s" % webhook_uri)

    # indicate where the API server will redirect the user after the user completes the authorization flow.
    # moet overeenkomen met een URI die opgezet is in Google console
    redirect_uri = settings.SITE_URL + reverse('GoogleDrive:oauth-webhook')

    # lees de json met de credentials
    flow = Flow.from_client_secrets_file(
                        CLIENT_ID_AND_SECRET,
                        scopes=SCOPES,
                        redirect_uri=redirect_uri,      # TODO: nodig?
                        state=transactie.unieke_code)

    my_logger.info("{handle_authentication_response} flow.code_verifier=%s" % repr(flow.code_verifier))
    my_logger.info("{handle_authentication_response} transactie.code_verifier=%s" % repr(transactie.code_verifier))

    try:
        host = settings.SITE_URL.replace('http://', 'https://')
        flow.fetch_token(
                    authorization_response=host + webhook_uri,
                    code_verifier=transactie.code_verifier)
    except AccessDeniedError as exc:
        # gebruiker heeft toestemming niet gegeven
        my_logger.error("{handle_authentication_response} AccessDeniedError: %s" % exc)
        token = None
    except OAuth2Error as exc:
        my_logger.error("{handle_authentication_response} OAuth2Error: %s" % exc)
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
