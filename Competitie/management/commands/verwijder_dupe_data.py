# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder de probleem data: dubbele schutterboog en te veel scores

from django.core.management.base import BaseCommand
from Competitie.models import RegioCompetitieSchutterBoog
from Score.models import Score, SCORE_TYPE_SCORE


class Command(BaseCommand):
    help = "Verwijder problematische data"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')

    def handle(self, *args, **options):

        dryrun = options['dryrun']

        gevonden = list()
        dupes = dict()

        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .select_related('deelcompetitie__competitie',
                                    'schutterboog')
                    .all()):
            tup = (obj.deelcompetitie.competitie.pk, obj.schutterboog.pk)
            if tup not in gevonden:
                gevonden.append(tup)
            else:
                if tup not in dupes:
                    dupes[tup] = obj
        # for

        for obj in dupes.values():
            self.stdout.write('Verwijder alle data voor %s in %s' % (obj.schutterboog, obj.deelcompetitie.competitie))

            # verwijder alle scores, niet-AG
            # dit zijn er typisch veel te veel
            scores = Score.objects.filter(schutterboog=obj.schutterboog, type=SCORE_TYPE_SCORE)
            self.stdout.write('   %s scores' % scores.count())
            if not dryrun:
                scores.delete()

            # verwijder alle dubbele deelnemers
            deelnemers = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__competitie=obj.deelcompetitie.competitie, schutterboog=obj.schutterboog)
            self.stdout.write('   %s deelnemers' % deelnemers.count())
            if not dryrun:
                deelnemers.delete()
        # for

# end of file
