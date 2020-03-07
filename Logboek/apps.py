# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig
from django.conf import settings
import logging

my_logger = logging.getLogger('NHBApps.Account')


class LogboekConfig(AppConfig):
    name = 'Logboek'

    def ready(self):
        # perform one-time startup logic

        # must import here to avoid AppRegistryNotReady exception
        from .models import LogboekRegel, schrijf_in_logboek

        msg = "Start met versie %s" % repr(settings.SITE_VERSIE)
        my_logger.info("UITROL " + msg)

        # schrijf het nieuw versienummer in het logboek
        if len(LogboekRegel.objects.filter(gebruikte_functie='Uitrol', activiteit=msg)) == 0:
            schrijf_in_logboek(None, 'Uitrol', msg)         # pragma: no cover


# end of file
