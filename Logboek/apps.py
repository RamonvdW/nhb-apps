# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


def post_migration_callback(sender, **kwargs):
    """ schrijf in het logboek na uitrol van een nieuwe versie """

    msg = "Start met versie %s" % repr(settings.SITE_VERSIE)

    # must import here to avoid AppRegistryNotReady exception
    from .models import LogboekRegel, schrijf_in_logboek

    # schrijf het nieuw versienummer in het logboek
    if LogboekRegel.objects.filter(gebruikte_functie='Uitrol', activiteit=msg).count() == 0:
        schrijf_in_logboek(None, 'Uitrol', msg)  # pragma: no cover


class LogboekConfig(AppConfig):
    """ Configuratie object van deze applicatie """

    name = 'Logboek'

    def ready(self):
        post_migrate.connect(post_migration_callback, sender=self)
        # perform one-time startup logic


# end of file
