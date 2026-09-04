# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .access_token import get_bearer_token
from .site import GraphSite
import requests


def _request_drives(out, site: GraphSite) -> list | None:

    if not get_bearer_token(out, site):
        out.write('[ERROR] {drives} No access token')
        return None

    out.write("[INFO] {drives} Requesting site drives")

    headers = {
        'Authorization': 'Bearer %s' % site.bearer_token,
        'Accept': 'application/json',
    }

    url = "https://graph.microsoft.com/v1.0/sites/%s/drives" % site.site_id

    try:
        resp = requests.get(url, headers=headers)

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie bij versturen get_drive_id request: %s" % str(exc))
    else:
        # out.write("[INFO] Full response: %s" % repr(resp.text))
        if resp.status_code != 200:
            out.write(
                "[ERROR] Get drive id request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                    repr(resp.encoding), repr(resp.status_code)))
            out.write("[ERROR] {drives} Full response: %s" % repr(resp.text))

        else:
            data = resp.json()
            # out.write("[INFO] Full json: %s" % repr(data))

            # {
            #     '@odata.context': 'https://graph.microsoft.com/v1.0/$metadata#drives',
            #     'value': [drive, ...]
            # }
            try:
                drives = data["value"]
            except KeyError:
                out.write("[ERROR] Missing value in response: %s" % repr(data))
            else:
                return drives

    return None


def get_drive_id(out, site: GraphSite) -> bool:

    if site.drive_id:
        return True

    # request the information
    drives = _request_drives(out, site)

    if drives is None:
        out.write('[ERROR] No drives')
        return False

    if len(drives) != 1:
        out.write('[ERROR] Expected 1 drive but got %s' % len(drives))
        for drive in drives:
            out.write('[DEBUG] Drive: %s' % repr(drive))
        # for
        return False

    drive = drives[0]

    """
        {
            'createdDateTime': '2026-03-01T23:24:15Z',
            'description': '',
            'id': '####',
            'lastModifiedDateTime': '2026-03-19T07:15:03Z',
            'name': 'Documents',
            'webUrl': 'https://####.sharepoint.com/sites/#name#/Shared%20Documents',
            'driveType': 'documentLibrary',
            'createdBy': {...},
            'lastModifiedBy': {
                'user': {...}
            },
            'owner': {
                'group': {...}
            },
            'quota': {
                'deleted': 0,
                'remaining': 27487788921712,
                'state': 'normal',
                'total': 27487790694400,
                'used': 1772688
            }
        }
    """

    try:
        site.drive_id = drive['id']
        site.drive_web_url = drive['webUrl']
    except KeyError:
        out.write("[ERROR] Not a complete drive response: %s" % repr(drive))
        site.drive_id = site.drive_web_url = ''
        return False

    return True


# end of file
