# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.utils.http import urlencode
from .site import GraphSite
from datetime import timedelta
import requests


def get_bearer_token(out, site: GraphSite) -> bool:

    """ Deze functie probeert een bearer token te krijgen aan de hand van een setje credentials

        out must provide a write() function that access a string and adds a newlines when called

        returns True if successful
    """

    now = timezone.now() + timedelta(seconds=30)
    if site.bearer_valid_until < now:
        site.bearer_token = ''

    if site.bearer_token:
        return True

    url = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % site.tenant_id

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    params = {
        "client_id": site.client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": site.client_secret,
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
        return False

    if resp.status_code != 200:
        out.write(
            "[ERROR] Access token request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                repr(resp.encoding), repr(resp.status_code)))
        out.write("[ERROR] Full response: %s" % repr(resp.text))
        return False

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

    try:
        if data["token_type"] != "Bearer":
            out.write("[ERROR] Not a bearer access token in %s" % repr(resp.text))
            return False

        token = data["access_token"]
        seconds = data["expires_in"]

        site.bearer_token = token
        site.bearer_valid_until = timezone.now() + timedelta(seconds=seconds)

    except KeyError:
        out.write("[ERROR] Not a complete bearer access token in %s" % repr(resp.text))
        return False

    return True

# end of file
