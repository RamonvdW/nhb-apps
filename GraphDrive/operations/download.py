# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from .access_token import get_bearer_token
from .drives import get_drive_id
from urllib.parse import quote
import requests

# https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems


def download(out, fpath: str, local_filename: str):
    """ Download a file from the Graph Drive """

    bearer_token = get_bearer_token(out)
    if not bearer_token:
        return None

    site_id = settings.GRAPH_SITE_ID
    drive_id, _ = get_drive_id(out)
    if not drive_id:
        return None

    url_fpath = quote(fpath)
    url = "https://graph.microsoft.com/v1.0/sites/%s/drives/%s/root:/%s:/content" % (site_id, drive_id, url_fpath)

    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
        'Accept': 'application/octet-stream',
        # TODO: something to prevent compression?
    }

    out.write('[DEBUG] {download} fpath=%s, url_fpath=%s' % (repr(fpath), repr(url_fpath)))
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            if r.status_code != 200:
                out.write(
                    "[ERROR] download request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                        repr(r.encoding), repr(r.status_code)))
                out.write("[ERROR] Full response: %s" % repr(r.text))
                return None

            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1*1024*1024):
                    f.write(chunk)
                # for
            # with

            return local_filename

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie tijdens download: %s" % str(exc))
        return None


# end of file
