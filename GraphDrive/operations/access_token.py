# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.utils.http import urlencode
from datetime import timedelta
import requests

_bearer_token = ''
_bearer_valid_until = timezone.now()


def clear_bearer_token():
    global _bearer_token, _bearer_valid_until
    _bearer_token = ''
    _bearer_valid_until = timezone.now()


def force_bearer_token(token, valid_until):
    global _bearer_token, _bearer_valid_until
    _bearer_token = token
    _bearer_valid_until = valid_until



def get_bearer_token(out) -> str | None:

    """ Deze functie probeert een bearer token te krijgen aan de hand van een setje credentials

        out must provide a write() function that access a string and adds a newlines when called
    """

    global _bearer_token, _bearer_valid_until

    now = timezone.now() + timedelta(seconds=30)
    if _bearer_valid_until < now:
        _bearer_token = ''

    if _bearer_token:
        return _bearer_token

    url = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % settings.GRAPH_TENANT_ID

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    params = {
        "client_id": settings.GRAPH_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": settings.GRAPH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    data = urlencode(params)

    out.write("[INFO] Requesting access token")

    try:
        resp = requests.post(
                        url,
                        headers=headers,
                        data=data)

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie bij versturen access token request: %s" % str(exc))
        return None

    if resp.status_code != 200:
        out.write(
            "[ERROR] Access token request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                repr(resp.encoding), repr(resp.status_code)))
        out.write("[ERROR] Full response: %s" % repr(resp.text))
        return None

    # out.write("[INFO] Full response: %s" % repr(resp.text))

    data = resp.json()
    """
        {
            "token_type": "Bearer",
            "expires_in": 3599,             
            "ext_expires_in": 3599,
            "access_token": "..."
        }
    """

    token = None
    try:
        if data["token_type"] != "Bearer":
            out.write("[ERROR] Not a bearer access token in %s" % repr(resp.text))
            return None

        token = data["access_token"]
        seconds = data["expires_in"]

        _bearer_token = token
        _bearer_valid_until = timezone.now() + timedelta(seconds=seconds)

    except KeyError:
        out.write("[ERROR] Not a complete bearer access token in %s" % repr(resp.text))
        return None

    return token


# end of file
