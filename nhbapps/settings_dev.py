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


if ENABLE_DJANGO_EXTENSIONS:                        # pragma: no cover
    INSTALLED_APPS.append('django_extensions')

if ENABLE_DEBUG_TOOLBAR:                            # pragma: no cover
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

    # fallback loader as requested by Debug Toolbar config check, but not really used
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

BETAAL_API = 'http://localhost:8125'


# end of file
