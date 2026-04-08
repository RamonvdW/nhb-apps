# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.apps import AppConfig
from Privacy.view_verklaring import laad_privacyverklaring


class PrivacyverklaringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Privacy'

    def ready(self):
        laad_privacyverklaring(settings.PRIVACYVERKLARING_FILE)


# end of file
