# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
Django settings for the NhbApps project during development runs and testing.
"""

from nhbapps.settings_base import *

DEBUG = True

ENABLE_DEBUG_TOOLBAR = False
#ENABLE_DEBUG_TOOLBAR = True

# django-extensions: very useful for show_urls
ENABLE_DJANGO_EXTENSIONS = False

# enable html validation using v.Nu (warning: triples test duration)
# warning: increases test run duration significantly
#TEST_VALIDATE_HTML = True


if ENABLE_DJANGO_EXTENSIONS:                        # pragma: no cover
    INSTALLED_APPS.append('django_extensions')

if ENABLE_DEBUG_TOOLBAR:                            # pragma: no cover
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

SAML_IDP_CONFIG['debug'] = DEBUG

# end of file
