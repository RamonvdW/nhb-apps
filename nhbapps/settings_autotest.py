# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated testing.
"""

from nhbapps.settings_base import *         # noqa

DEBUG = True
ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False

# significant speed up by reducing calculation time for secure password handling
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

WEBWINKEL_FOTOS_DIR = 'data_test/webwinkel'

# enable html validation using v.Nu (warning: triples test duration)
# warning: increases test run duration significantly
#TEST_VALIDATE_HTML = True

# end of file
