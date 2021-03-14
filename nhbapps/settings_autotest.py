# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated testing.
"""

from nhbapps.settings_base import *

DEBUG = True
ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False
SAML_IDP_CONFIG['debug'] = DEBUG

# end of file
