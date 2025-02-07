# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Instaptoets vragen inladen uit een JSON file (download van Google Sheets) """

from django.core.management.base import BaseCommand
from Instaptoets.models import Instaptoets
from Sporter.models import Sporter
import datetime


class Command(BaseCommand):
    help = "Zet de instaptoets als gehaald voor iemand"

    def __init__(self):
        super().__init__()
        self.sporter = None
        self.datum = None

    def add_arguments(self, parser):
        parser.add_argument('bondsnummer', type=int, help="Bondsnummer van de sporter")
        parser.add_argument('datum', type=str, help="Op welke datum gehaald? (YYYY-MM-DD)")

    def _get_sporter(self, lid_nr: int):
        try:
            self.sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            self.stderr.write('[ERROR] Sporter met bondsnummer %s niet gevonden' % repr(lid_nr))

    def _get_datum(self, datum_str):
        try:
            datum_gehaald = datetime.datetime.strptime(datum_str, '%Y-%m-%d')
        except ValueError:
            self.stderr.write('[ERROR] %s is geen valide datum. Moet voldoen aan YYYY-MM-DD' % repr(datum_str))
        else:
            # print('datum_gehaald: %s' % repr(datum_gehaald))
            delta = datetime.datetime.now() - datum_gehaald
            if 1 <= delta.days <= 365:
                self.datum = datum_gehaald.replace(tzinfo=datetime.timezone.utc)
            else:
                self.stderr.write('[ERROR] Datum moet in de afgelopen 365 dagen liggen')

    def _zet_fake_gehaald(self):
        instaptoets = Instaptoets(
                        afgerond=self.datum,
                        sporter=self.sporter,
                        is_afgerond=True,
                        geslaagd=True)
        instaptoets.save()
        instaptoets.opgestart = self.datum
        instaptoets.save(update_fields=['opgestart'])

        self.stdout.write('[INFO] Instaptoets afgerond + geslaagd voor %s' % self.sporter)

    def handle(self, *args, **options):
        self._get_sporter(options['bondsnummer'])
        self._get_datum(options['datum'])

        if self.sporter and self.datum:
            self._zet_fake_gehaald()


# end of file
