# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during development runs.

    this file is included by django.conf.settings

    Normal:       (wsgi.py or ./manage.py cmd)
      SiteMain/settings.py
          includes SiteMain/core/settings_base.py
              includes SiteMain/settings_local.py for site specific settings  <-- replaced on real deployment
          provides additional items that are part of the release

    Autotest via test.sh  (uses ./manage.py cmd --settings=SiteMain.settings_autotest)
      SiteMain/settings_autotest[_nodebug].py
          includes SiteMain/core/settings_base.py
              includes SiteMain/settings_local.py for site specific settings
          provides additional items that are part of the release
      provides changes to to settings for autotest

    Dev server via run.sh  (uses ./manage.py cmd --settings=SiteMain.settings_dev)
      SiteMain/settings_dev.py
          includes SiteMain/core/settings_base.py
              includes SiteMain/settings_local.py for site specific settings
          provides additional items that are part of the release
      provides changes to to settings for autotest
"""

from SiteMain.core.settings_base import *         # noqa

ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False
DEBUG = True

# disable use of subset files in dev, to simplify introduction of new icons
USE_SUBSET_FONT_FILES = False

# debug toolbar for database access analysis
# ENABLE_DEBUG_TOOLBAR = True


# django-extensions
#   very useful for show_urls:
#     ./manage.py show_urls --settings=SiteMain.settings_dev --format table | cut -d\| -f1
# ENABLE_DJANGO_EXTENSIONS = True


# ask the template engine to insert a special pattern in the output in case of template problems
TEMPLATES[0]['OPTIONS']['string_if_invalid'] = '##BUG %s ##'


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

# end of file
