# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class TijdelijkeCodesConfig(AppConfig):

    name = 'TijdelijkeCodes'
    verbose_name = "Tijdelijke codes"

    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # inject the save function to the operations library
        from TijdelijkeCodes.operations import set_tijdelijke_code_saver
        from TijdelijkeCodes.models import save_tijdelijke_code

        set_tijdelijke_code_saver(save_tijdelijke_code)


# end of file
