# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class NhbStructuurConfig(AppConfig):
    name = 'NhbStructuur'
    verbose_name = "Nhb structuur"

    def ready(self):
        # geef de view code een kans de plugins te registreren
        import NhbStructuur.views

# end of file
