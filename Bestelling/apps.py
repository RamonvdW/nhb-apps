# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class BestellingConfig(AppConfig):
    """ Configuratie object van deze applicatie """

    name = 'Bestelling'

    default_auto_field = 'django.db.models.BigAutoField'


# end of file
