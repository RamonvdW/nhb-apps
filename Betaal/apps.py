# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class BetaalConfig(AppConfig):
    """ Configuratie object van deze applicatie """

    name = 'Betaal'

    default_auto_field = 'django.db.models.BigAutoField'

# end of file
