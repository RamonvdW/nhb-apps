# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


def post_migration_callback(sender, **kwargs):
    """ schrijf in het logboek na uitrol van een nieuwe versie """

    msg = "Start met versie %s op %s" % (repr(settings.SITE_VERSIE), repr(settings.SITE_URL))

    # must import here to avoid AppRegistryNotReady exception
    from Logboek.models import LogboekRegel, schrijf_in_logboek

    # schrijf het nieuw versienummer in het logboek
    if LogboekRegel.objects.filter(gebruikte_functie='Uitrol', activiteit=msg).count() == 0:
        schrijf_in_logboek(None, 'Uitrol', msg)  # pragma: no cover


class LogboekConfig(AppConfig):
    """ Configuratie object van deze applicatie """

    name = 'Logboek'

    def ready(self):
        # perform one-time startup logic

        # koppel aan de callback als het 'migrate' commando klaar is
        # in de callback schrijven we een regel in het logboek
        post_migrate.connect(post_migration_callback, sender=self)


# end of file
