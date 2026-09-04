# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .access_token import get_bearer_token
from .drives import get_drive_id
from .site import GraphSite
from urllib.parse import quote
from typing import Tuple
import requests

# https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems


def list_folders_and_files(out, site: GraphSite, folder: str) -> Tuple[list[str], list[str]] | Tuple[None, None]:
    """ List the files available in a Graph Drive folder

        folder: subfolder, like "General"
                use "/" to list the contents of the root folder

        returns a list of folders + a list of files
                or None, None in case of an error
                list of files is (last modified timestamp, size, name, item-id)
                    item-id is needed by delete()
    """

    if not get_bearer_token(out, site):
        return None, None

    if not get_drive_id(out, site):
        return None, None

    url_folder = quote(folder)
    url = "https://graph.microsoft.com/v1.0/sites/%s/drives/%s/root:/%s:/children" % (site.site_id, site.drive_id, url_folder)

    headers = {
        'Authorization': 'Bearer %s' % site.bearer_token,
        'Accept': 'application/json',
    }

    out.write('[DEBUG] {list} folder=%s, url_folder=%s' % (repr(folder), repr(url_folder)))
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            if r.status_code != 200:
                out.write(
                    "[ERROR] list request gaf onverwacht antwoord! response encoding:%s, status_code:%s" % (
                        repr(r.encoding), repr(r.status_code)))
                out.write("[ERROR] Full response: %s" % repr(r.text))
                return None, None

            data = r.json()

            try:
                files = data["value"]
            except KeyError:
                out.write("[ERROR] Missing value in response: %s" % repr(data))
            else:
                dir_lijst = []
                file_lijst = []
                for file_d in files:
                    #out.write('[DEBUG] file_d: %s' % repr(file_d))
                    if 'folder' in file_d:
                        # directory
                        dir_lijst.append(file_d['name'])
                    else:
                        # file
                        tup = (file_d['lastModifiedDateTime'], file_d['size'], file_d['name'], file_d['id'])
                        file_lijst.append(tup)
                # for
                return dir_lijst, file_lijst

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        out.write("[ERROR] Exceptie tijdens l: %s" % str(exc))
        return None, None

    return None, None


# end of file
