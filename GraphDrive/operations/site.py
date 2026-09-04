# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

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

    def __init__(self, tenant_id: str, site_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id              # company
        self.site_id = site_id                  # sharepoint site
        self.client_id = client_id              # application
        self.client_secret = client_secret

        # will be retrieved upon first use
        self.bearer_token = ''
        self.bearer_valid_until = timezone.now()
        self.drive_id = ''
        self.drive_web_url = ''

# end of file
