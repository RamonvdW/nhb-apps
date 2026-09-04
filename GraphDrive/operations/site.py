# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone

"""
    This class represents one site with a specific client to access it,
    thus allowing multiple sites for one tenant.
"""

class GraphSite:

    """
        out: must provide a write() function that access a string and adds a newlines when called
        site_id: the ID presentating the site within the tenant
        client_id: ID representing the application (aka App ID)
        client_secret: the secret for client_id
    """

    def __init__(self, out):
        self.out = out

        # will be set by setup
        self.tenant_id = ''
        self.site_id = ''
        self.client_id = ''
        self.client_secret = ''

        # will be retrieved upon first use
        self.bearer_token = ''
        self.bearer_valid_until = timezone.now()
        self.drive_id = ''
        self.drive_web_url = ''

    def setup(self, site_index: int) -> bool:
        try:
            ids = settings.GRAPH_IDS[site_index]
        except KeyError:
            self.out.write('[ERROR] Kan site index %s niet vinden in GRAPH_IDS' % site_index)
            return False

        self.tenant_id = settings.GRAPH_IDS['tenant_id']    # company
        self.site_id = ids['site_id']                       # sharepoint site
        self.client_id = ids['client_id']                   # application
        self.client_secret = ids['client_secret']

        print(repr(self.tenant_id), repr(self.site_id), repr(self.client_id), repr(self.client_secret))

        return True


# end of file
