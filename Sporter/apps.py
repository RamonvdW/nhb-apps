# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class SporterConfig(AppConfig):
    name = 'Sporter'

    def ready(self):
        # laat de plugin zich registeren
        import Sporter.login_plugin


# end of file
