# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder de probleem data: dubbele sporterboog en te veel scores

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieSporterBoog
from Score.definities import SCORE_TYPE_SCORE
from Score.models import Score


class Command(BaseCommand):
    help = "Verwijder problematische data"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true')

    def handle(self, *args, **options):

        do_commit = options['commit']

        gevonden = list()
        dupes = dict()

        for obj in (RegiocompetitieSporterBoog
                    .objects
                    .select_related('regiocompetitie__competitie',
                                    'sporterboog')
                    .all()):
            tup = (obj.regiocompetitie.competitie.pk, obj.sporterboog.pk)
            if tup not in gevonden:
                gevonden.append(tup)
            else:
                if tup not in dupes:
                    dupes[tup] = obj
        # for

        uitleggen = False

        for obj in dupes.values():
            self.stdout.write('Verwijder alle data voor deelnemer %s in %s' % (obj.sporterboog, obj.regiocompetitie.competitie))

            # verwijder alle scores, niet-AG
            # dit zijn er typisch veel te veel
            scores = Score.objects.filter(sporterboog=obj.sporterboog, type=SCORE_TYPE_SCORE)
            self.stdout.write('   %s scores' % scores.count())
            if do_commit:
                scores.delete()
            else:
                uitleggen = True

            # verwijder alle dubbele deelnemers
            deelnemers = RegiocompetitieSporterBoog.objects.filter(regiocompetitie__competitie=obj.regiocompetitie.competitie, sporterboog=obj.sporterboog)
            self.stdout.write('   %s deelnemers' % deelnemers.count())
            if do_commit:
                deelnemers.delete()
            else:
                uitleggen = True
        # for

        if uitleggen:
            self.stderr.write('Gebruik --commit om bovenstaande voorstellen echt te verwijderen')
        else:
            self.stdout.write('Geen duplicate data gevonden')

# end of file
