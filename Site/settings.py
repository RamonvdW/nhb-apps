# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project for Server deployment.

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

# end of file
