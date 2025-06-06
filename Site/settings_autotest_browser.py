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

    Autotest via browser_test.sh  (uses ./manage.py cmd --settings=Site.settings_autotest_browser)
      Site/settings_autotest_browser.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
              provides additional items that are part of the release
          provides changes to to settings for autotest with remote browser

    Dev server via run.sh  (uses ./manage.py cmd --settings=Site.settings_dev)
      Site/settings_dev.py
          includes Site/core/settings_base.py
              includes Site/settings_local.py for site specific settings
              provides additional items that are part of the release
          provides changes to to settings for dev
"""

from Site.settings_autotest import *         # noqa

# useless because Django forces DEBUG=False anyway
DEBUG = False

# this configuration is used by browser_tests.sh
# enable instrumentation of javascript
ENABLE_MINIFY = False                   # used in Site/core/minify_dtl.py and Site/core/transpose_js.py
ENABLE_INSTRUMENT_JS = True             # used in Site/core/instrument_js.py

# disable some features, to increase coverage
USE_SUBSET_FONT_FILES = False           # impacts site_layout_fonts.dtl
TOON_LEDENVOORDEEL = False

# end of file
