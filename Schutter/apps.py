# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class SchutterConfig(AppConfig):
    name = 'Schutter'

    def ready(self):
        # geef de code een kans om de plugin te registeren
        import Schutter.leeftijdsklassen

# end of file
