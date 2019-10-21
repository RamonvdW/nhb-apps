# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
Django local settings for the nhba-apps project.

This file is included from settings.py and contains specific
settings that can be changed as part of a deployment, without
having to edit the settings.py file.
"""

# SECURITY WARNING: keep the secret key used in production secret!
# TODO: uitzoeken waarom en hoe dit in elkaar steekt
SECRET_KEY = '1234-replace-with-your-own-secret-key-56789abcdefg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1'
]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database-name',
        'USER': 'database-user',
        'PASSWORD': 'database-pwd',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# end of file

