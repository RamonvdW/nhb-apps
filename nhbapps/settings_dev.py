# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during development runs.
"""

from nhbapps.settings_base import *

ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False
DEBUG = True


# debug toolbar for database access analysis
#ENABLE_DEBUG_TOOLBAR = True


# django-extensions
#   very useful for show_urls:
#     ./manage.py show_urls --settings=nhbapps.settings_dev
#ENABLE_DJANGO_EXTENSIONS = True


# enable html validation using v.Nu (warning: triples test duration)
# warning: increases test run duration significantly
#TEST_VALIDATE_HTML = True


if ENABLE_DJANGO_EXTENSIONS:                        # pragma: no cover
    INSTALLED_APPS.append('django_extensions')

if ENABLE_DEBUG_TOOLBAR:                            # pragma: no cover
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# end of file
