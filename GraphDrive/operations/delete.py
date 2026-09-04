# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .access_token import get_bearer_token
from .site import GraphSite
import requests

# https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems


def delete_item(out, site: GraphSite, item_id: str):
    """ Delete a file from the Graph Drive

        item-id: id of the item as returned by list()
    """

    if not get_bearer_token(out, site):
        return None, None

    url = "https://graph.microsoft.com/v1.0/sites/%s/drive/items/%s" % (site.site_id, item_id)

    headers = {
        'Authorization': 'Bearer %s' % site.bearer_token,
        'Accept': 'application/json',
    }

    out.write('[DEBUG] {delete} item_id=%s' % repr(item_id))
    try:
        with requests.delete(url, headers=headers) as r:
            if r.status_code != 204:        # 204 No Content is succes indicator
                out.write(
                    "[ERROR] delete request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                        repr(r.encoding), repr(r.status_code)))
                out.write("[ERROR] Full response: %s" % repr(r.text))

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie tijdens l: %s" % str(exc))


# end of file
