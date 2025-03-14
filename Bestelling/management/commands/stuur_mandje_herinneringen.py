# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" management commando dat 1x per dag gedraaid wordt (crontab) om een e-mail te sturen als herinnering
    aan producten die nog in het mandje liggen maar niet omgezet zijn in een bestelling.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from Bestelling.models import BestellingMandje
from Mailer.operations import mailer_queue_email, render_email_template

EMAIL_TEMPLATE_HERINNERING_MANDJE = 'email_bestelling/herinnering-mandje.dtl'


class Command(BaseCommand):

    help = "Stuur herinnering producten in mandje"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    @staticmethod
    def _stuur_herinnering(account, num_prod):
        """ Stuur een e-mail """

        context = {
            'voornaam': account.get_first_name(),
            'naam_site': settings.NAAM_SITE,
            'num_prod': num_prod,
        }

        mail_body = render_email_template(context, EMAIL_TEMPLATE_HERINNERING_MANDJE)

        mailer_queue_email(account.bevestigde_email,
                           'Producten in mandje op MijnHandboogsport',
                           mail_body)

    def handle(self, *args, **options):

        for mandje in (BestellingMandje
                       .objects
                       .annotate(num_regels=Count('regels'))
                       .exclude(num_regels=0)):

            self.stdout.write('[INFO] Mandje met producten: %s' % mandje)

            self._stuur_herinnering(mandje.account, mandje.num_producten)

        # for


# end of file
