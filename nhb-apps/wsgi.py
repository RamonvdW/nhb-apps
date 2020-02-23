# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
WSGI config for the nhb-apps project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys
import time
import signal
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhb-apps.settings')

application = get_wsgi_application()
#try:
#    application = get_wsgi_application()
#except Exception:
#    if 'mod_wsgi' in sys.modules:
#        traceback.print_exc()
#        os.kill(os.getpid(), signal.SIGINT)
#        time.sleep(2.5)

# end of file
