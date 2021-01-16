# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# corrigeer de HistCompetitieIndividueel records: totaal en ranking

from django.core.management.base import BaseCommand
from HistComp.models import HistCompetitie, HistCompetitieIndividueel


class Command(BaseCommand):
    help = "Corrigeer historische competitie uitslag, individueel"

    @staticmethod
    def _corrigeer(histcomp):
        alle = list()
        for obj in (HistCompetitieIndividueel
                    .objects
                    .filter(histcompetitie=histcomp)):

            scores = [obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7]
            scores.sort(reverse=True)       # hoogste eerst

            obj.totaal = sum(scores[:6])    # totaal over 6 scores (was: 7)

            tup = (obj.gemiddelde,
                   scores,
                   len(alle),           # deze voorkomt sorteren op obj
                   obj)
            alle.append(tup)
        # for

        alle.sort(reverse=True)             # hoogste gemiddelde eerst

        rank = 1
        for _, _, _, obj in alle:
            obj.rank = rank
            obj.save()
            rank += 1
        # for

    def handle(self, *args, **options):
        for histcomp in HistCompetitie.objects.all():
            self.stdout.write('Corrigeer %s - %sm - %s' % (histcomp.seizoen, histcomp.comp_type, histcomp.klasse))
            self._corrigeer(histcomp)
        # for

# end of file
