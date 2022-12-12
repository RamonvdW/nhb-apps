# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django settings for the NhbApps project during automated testing.
"""

from nhbapps.settings_base import *         # noqa

DEBUG = False

# significant speed up by reducing calculation time for secure password handling
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# end of file
