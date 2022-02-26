# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# schoon een aantal tabellen in de database op
# deze taak wordt een keer per week gedraaid

from django.core.management.base import BaseCommand
from Account.models import accounts_opschonen
from Feedback.models import feedback_opschonen
from Logboek.models import logboek_opschonen
from Mailer.models import mailer_opschonen
from Overig.models import overig_opschonen
from Taken.models import taken_opschonen


class Command(BaseCommand):
    help = "Verwijder oude data uit de database (1x per dag aanroepen)"

    def handle(self, *args, **options):

        accounts_opschonen(self.stdout)
        feedback_opschonen(self.stdout)
        logboek_opschonen(self.stdout)
        mailer_opschonen(self.stdout)
        overig_opschonen(self.stdout)
        taken_opschonen(self.stdout)

        self.stdout.write('Klaar')

# end of file
