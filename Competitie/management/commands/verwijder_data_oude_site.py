# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from django.utils import timezone
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid, NhbVereniging
from Logboek.models import schrijf_in_logboek
from Competitie.models import DeelcompetitieRonde
from Schutter.models import SchutterBoog
from Wedstrijden.models import Wedstrijd, WedstrijdUitslag, WedstrijdenPlan
from Score.models import Score, ScoreHist
from decimal import Decimal
import datetime
import sys
import os


class Command(BaseCommand):
    help = "Data van de oude site verwijderen"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def verwijder_uitslag(self, uitslag):
        # verwijder deze wedstrijduitslag en alle onderliggende data
        self.stdout.write('verwijder %s scores' % uitslag.scores.count())
        uitslag.scores.all().delete()
        self.stdout.write('verwijder uitslag %s' % uitslag.pk)
        uitslag.delete()

    def verwijder_wedstrijd(self, wedstrijd):
        # verwijder deze wedstrijd en alle onderliggende data
        if wedstrijd.uitslag:
            uitslag = wedstrijd.uitslag
            wedstrijd.uitslag = None
            wedstrijd.save()
            self.verwijder_uitslag(uitslag)
        self.stdout.write('verwijder wedstrijd %s' % wedstrijd.pk)
        wedstrijd.delete()

    def verwijder_plan(self, plan):
        # verwijder dit wedstrijdenplan en alle onderliggende data
        for wedstrijd in plan.wedstrijden.all():
            self.verwijder_wedstrijd(wedstrijd)
        # for
        self.stdout.write('verwijder plan %s' % plan.pk)
        plan.delete()

    def verwijder_ronde(self, ronde):
        # verwijder deze deelcompetitieronde en alle onderliggende data
        plan = ronde.plan
        self.stdout.write('verwijder ronde %s' % ronde.pk)
        ronde.delete()
        self.verwijder_plan(plan)

    def handle(self, *args, **options):
        for ronde in DeelcompetitieRonde.objects.all():
            if ronde.is_voor_import_oude_programma():
                self.verwijder_ronde(ronde)
        # for

        activiteit = 'Alle eerder ingelezen data van het oude programma zijn verwijderd'

        # schrijf in het logboek
        schrijf_in_logboek(account=None,
                           gebruikte_functie='verwijder_data_oude_site (command line)',
                           activiteit=activiteit)
        self.stdout.write(activiteit)

# end of file
