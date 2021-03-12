# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during testing.
"""

from nhbapps.settings_base import *

DEBUG = True                    # generate coverage for the logic behind debug mode
ENABLE_WIKI = True              # test with the wiki logic enabled

# single sign-on Identity Provider (IP)
#   using SAML2 (Security Assertion Markup Language)
INSTALLED_APPS.append('djangosaml2idp')

WIKI_URL = SITE_URL

# end of file
