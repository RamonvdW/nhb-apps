# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class SporterConfig(AppConfig):
    name = 'Sporter'

    def ready(self):
        # laat de plugin zich registeren
        import Sporter.view_login_plugin


# end of file
