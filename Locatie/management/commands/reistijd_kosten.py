# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from django.utils import timezone
from Locatie.models import WedstrijdLocatie, Reistijd
from Sporter.models import Sporter
import datetime


class Command(BaseCommand):

    help = "Reistijden kosten voorspellen"

    def __init__(self):
        super().__init__()

    def _distributie(self):
        datums = list(Reistijd.objects.order_by('op_datum').values_list('op_datum', flat=True))

        counts = dict()
        for datum in datums:
            tup = (datum.year, datum.month)
            try:
                counts[tup] += 1
            except KeyError:
                counts[tup] = 1
        # for

        for tup in sorted(counts.keys()):
            year, month = tup
            self.stdout.write('%d-%02d %5d' % (year, month, counts[tup]))
        # for

        self.stdout.write('')

        totaal = sum(counts.values())
        self.stdout.write('Aantal records: %s' % totaal)
        aantal = len(counts) - 1        # eerste en laatste maand zijn partieel
        aantal = max(1, aantal)         # voorkom delen door 0
        gemiddelde = int(round(totaal / aantal))

        self.stdout.write('Gemiddelde: %d per maand' % gemiddelde)
        self.stdout.write('(free tier: 3000/maand)')

    def handle(self, *args, **options):
        self._distributie()


# end of file
