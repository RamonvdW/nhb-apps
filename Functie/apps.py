# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class FunctieConfig(AppConfig):
    name = 'Functie'

    def ready(self):
        # laat de plugin zich registeren
        import Functie.plugins


# end of file
