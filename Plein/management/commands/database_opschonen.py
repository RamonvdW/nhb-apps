# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# schoon een aantal tabellen in de database op
# deze taak wordt een keer per week gedraaid

from django.core.management.base import BaseCommand
from Account.operations.opschonen import accounts_opschonen
from Beheer.views import beheer_opschonen
from Bestelling.operations.opschonen import bestel_opschonen
from Betaal.operations import betaal_opschonen
from Feedback.models import feedback_opschonen
from Logboek.models import logboek_opschonen
from Mailer.models import mailer_opschonen
from Registreer.operations import registreer_opschonen
from Taken.models import taken_opschonen
from TijdelijkeCodes.models import tijdelijke_url_opschonen


class Command(BaseCommand):
    help = "Verwijder oude data uit de database (1x per dag aanroepen)"

    def handle(self, *args, **options):

        bestel_opschonen(self.stdout)
        betaal_opschonen(self.stdout)
        beheer_opschonen(self.stdout)
        feedback_opschonen(self.stdout)
        logboek_opschonen(self.stdout)
        mailer_opschonen(self.stdout)
        taken_opschonen(self.stdout)
        tijdelijke_url_opschonen(self.stdout)
        registreer_opschonen(self.stdout)
        accounts_opschonen(self.stdout)
        # TODO: opleiding
        # TODO: scheidsrechters

        self.stdout.write('Klaar')

# end of file
