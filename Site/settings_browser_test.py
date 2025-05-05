# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated browser testing.

    Browser testing via browser_test.sh  (uses ./manage.py runserver --settings=Site.settings_browser_test)
      Site/settings_browser_test.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
          provides additional items
      provides changes to to settings for browser testing
"""

from Site.core.settings_base import *         # noqa

# required for runserver to serve static files
DEBUG = True

# significant speed up by reducing calculation time for secure password handling
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

WEBWINKEL_FOTOS_DIR = 'Webwinkel/test-files/'

# Mollie endpoint URL override
BETAAL_API_URL = 'http://localhost:8125'        # gebruik de simulator

# zet minify aan (net als op de echte server)
ENABLE_MINIFY = True

# change to the test database manually, comparable to what ./manage.py test does
# this is required for the runserver command
DATABASES['default']['NAME'] = 'test_' + DATABASES['default']['NAME']

# end of file
