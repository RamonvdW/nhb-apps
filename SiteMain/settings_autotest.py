# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated testing.

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

DEBUG = True
ENABLE_DEBUG_TOOLBAR = False
ENABLE_DJANGO_EXTENSIONS = False

# ask the template engine to insert a special pattern in the output in case of template problems
TEMPLATES[0]['OPTIONS']['string_if_invalid'] = '##BUG %s ##'

# significant speed up by reducing calculation time for secure password handling
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

WEBWINKEL_FOTOS_DIR = 'Webwinkel/test-files/'

# enable javascript validation using ESprima
TEST_VALIDATE_JAVASCRIPT = True

# enable html validation using the Nu Html Checker (v.Nu)
# WARNING: increases test run duration significantly (triple!)
#TEST_VALIDATE_HTML = True


# end of file
