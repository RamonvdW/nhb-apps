# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from .access_token import get_bearer_token
from .drives import get_drive_id
from urllib.parse import quote
import requests


def get_file_metadata(out, fpath: str) -> dict | None:
    """ Get the metadata for a file """

    bearer_token = get_bearer_token(out)
    if not bearer_token:
        return None

    site_id = settings.GRAPH_SITE_ID
    drive_id, _ = get_drive_id(out)
    if not drive_id:
        return None

    url_fpath = quote(fpath)
    url = "https://graph.microsoft.com/v1.0/sites/%s/drives/%s/root:/%s" % (site_id, drive_id, url_fpath)

    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
        'Accept': 'application/json',
    }

    out.write('[DEBUG] {get_file_metadata} fpath=%s, url_fpath=%s' % (repr(fpath), repr(url_fpath)))
    try:
        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            out.write(
                "[ERROR] {get_file_metadata} request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                                    repr(resp.encoding), repr(resp.status_code)))
            out.write("[ERROR] Full response: %s" % repr(resp.text))
            return None
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] {get_file_metadata} Exceptie tijdens request: %s" % str(exc))
        return None

    """
        {
            '@odata.context': 'https://graph.microsoft.com/v1.0/$metadata#Collection(driveItem)/$entity',
            '@microsoft.graph.downloadUrl': 'https://####.sharepoint.com/sites/####/_layouts/15/download.aspx?UniqueId=###&Translate=false&tempauth=v1.###&ApiVersion=2.0',
            'createdBy': {...},
            'createdDateTime': '2026-03-19T07:24:08Z',
            'eTag': '###',
            'id': '###',
            'lastModifiedBy': {...},
            'lastModifiedDateTime': '2026-04-05T19:10:08Z',
            'name': 'Test.xlsx',
            'parentReference': {
                'driveType': 'documentLibrary',
                'driveId': '####',
                'id': '###',
                'name': 'General',
                'path': '/drives/###/root:/General',
                'siteId': '###'
            },
            'webUrl': 'https://####.sharepoint.com/sites/###/_layouts/15/Doc.aspx?sourcedoc=###&file=Test.xlsx&action=default&mobileredirect=true',
            'cTag': '###',
            'file': {
                'fileExtension': '.xlsx',
                'hashes': {
                    'quickXorHash': '###'
                },
                'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            'fileSystemInfo': {
                'createdDateTime': '2026-03-19T07:24:08Z',
                'lastModifiedDateTime': '2026-04-05T19:10:08Z'
            },
            'isAuthoritative': False,
            'shared': {
                'scope': 'users'
            },
            'size': 12310
        }
    """

    return resp.json()


def get_file_last_modified(out, fpath: str) -> str:
    """ Get the last modified date/time for a file """

    data = get_file_metadata(out, fpath)
    out.write("[INFO] {get_last_modified} data=%s" % repr(data))

    last_mod = ''
    if data:
        last_mod = data['lastModifiedDateTime']

    return last_mod


# end of file
