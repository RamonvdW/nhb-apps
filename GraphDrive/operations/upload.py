# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .access_token import get_bearer_token
from .drives import get_drive_id
from .site import GraphSite
from urllib.parse import quote
import requests

# https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems


def upload_file(out, site: GraphSite, local_filename: str, remote_fpath: str):
    """ Upload a file to the Graph Drive """

    if not get_bearer_token(out, site):
        return None

    if not get_drive_id(out, site):
        return None

    url_fpath = quote(remote_fpath)
    url = "https://graph.microsoft.com/v1.0/sites/%s/drives/%s/root:/%s:/content" % (site.site_id, site.drive_id, url_fpath)

    headers = {
        'Authorization': 'Bearer %s' % site.bearer_token,
        'Content-Type': 'application/gzip',
        'Accept': 'application/json',
    }

    out.write('[DEBUG] {upload} fpath=%s, url_fpath=%s' % (repr(remote_fpath), repr(url_fpath)))
    try:
        f = open(local_filename, 'rb')
        with requests.put(url, data=f, headers=headers, stream=False) as r:
            if r.status_code != 201:        # 201 Created is het normale antwoord
                out.write(
                    "[ERROR] upload request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                        repr(r.encoding), repr(r.status_code)))
                out.write("[ERROR] Full response: %s" % repr(r.text))
                return None

            out.write('[DEBUG] {upload} is gelukt')
            return "OK"

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie tijdens download: %s" % str(exc))
        return None


# end of file
