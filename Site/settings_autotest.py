# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated testing.

    this file is included by django.conf.settings

    Normal:       (wsgi.py or ./manage.py cmd)
      Site/settings.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings  <-- replaced on real deployment
              provides additional items that are part of the release

    Autotest via test.sh  (uses ./manage.py cmd --settings=Site.settings_autotest)
      Site/settings_autotest[_nodebug].py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
              provides additional items that are part of the release
          provides changes to to settings for autotest

    Dev server via run.sh  (uses ./manage.py cmd --settings=Site.settings_dev)
      Site/settings_dev.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
              provides additional items that are part of the release
          provides changes to to settings for dev
"""

from Site.core.settings_base import *         # noqa

# DEBUG = True is required for runserver to serve static files
DEBUG = True

# ask the template engine to insert a special pattern in the output in case of template problems
# pattern is detected in html_assert_template_bug in TestHelpers/test_asserts.py
TEMPLATES[0]['OPTIONS']['string_if_invalid'] = '##BUG %s ##'

# template debugging must be enabled for coverage measurement with django-coverage-plugin
TEMPLATES[0]['OPTIONS']['debug'] = True

# significant speed up by reducing calculation time for secure password handling
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

WEBWINKEL_FOTOS_DIR = 'Webwinkel/test-files/'
STATICFILES_DIRS = [
    ("webwinkel_fotos", WEBWINKEL_FOTOS_DIR),       # noqa
]

KALENDER_API_TOKENS = ('autotest',)

# Mollie endpoint URL override
BETAAL_API_URL = 'http://localhost:8125'        # gebruik de simulator

# enable javascript validation using ESprima
TEST_VALIDATE_JAVASCRIPT = True

# enable html validation using the Nu Html Checker (v.Nu)
# WARNING: increases test run duration significantly (triple!)
#TEST_VALIDATE_HTML = True

# zet minify uit ivm coverage meting van de template files
# (die kan niet tegen aanpassing ten opzicht van source files)
# om toch MET minify te testen doen we dit tijdens HTML validatie
ENABLE_MINIFY = TEST_VALIDATE_HTML

# end of file
