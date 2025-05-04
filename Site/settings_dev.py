# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during development runs.

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

    Browser testing via browser_test.sh  (uses ./manage.py runserver --settings=Site.settings_browser_test)
      Site/settings_browser_test.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
          provides additional items
      provides changes to to settings for browser testing

    Dev server via run.sh  (uses ./manage.py cmd --settings=Site.settings_dev)
      Site/settings_dev.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
          provides additional items that are part of the release
      provides changes to to settings for dev
"""

from Site.core.settings_base import *         # noqa

# required for runserver to serve static files
DEBUG = True

# disable use of subset files in dev, to simplify introduction of new icons
USE_SUBSET_FONT_FILES = False

# debug toolbar for database access analysis
# ENABLE_DEBUG_TOOLBAR = True

# disable minify for debugging (default = True)
# ENABLE_MINIFY = False

# django-extensions
#   very useful for show_urls:
#     ./manage.py show_urls --settings=Site.settings_dev --format table | cut -d\| -f1
# ENABLE_DJANGO_EXTENSIONS = True


# ask the template engine to insert a special pattern in the output in case of template problems
TEMPLATES[0]['OPTIONS']['string_if_invalid'] = '##BUG %s ##'

# significant speed up by reducing calculation time for secure password handling
# (use during debugging of autotesters)
# PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Mollie endpoint URL override
BETAAL_API_URL = 'http://localhost:8125'        # gebruik de simulator

if ENABLE_DJANGO_EXTENSIONS:                        # pragma: no cover
    INSTALLED_APPS.append('django_extensions')

if ENABLE_DEBUG_TOOLBAR:                            # pragma: no cover
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

    # fallback loader as requested by Debug Toolbar config check
    TEMPLATES.append(
        {
            'NAME': 'default',
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            # 'DIRS': [ str(APPS_DIR.path('templates')), ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',  # permission checking
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }
    )

INSTAPTOETS_AANTAL_VRAGEN = 2

# end of file
