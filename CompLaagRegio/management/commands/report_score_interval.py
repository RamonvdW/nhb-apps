# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieSporterBoog, Regiocompetitie
from Score.models import Score, ScoreHist


class Command(BaseCommand):
    help = "Toon interval van genoteerde scores in een regio"

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=int, help='Competitie afstand (18 of 25)', choices={18, 25})
        parser.add_argument('regio_nr', type=int, help='Regio nummer (101..116)', choices={*range(101, 116+1)})

    def handle(self, *args, **options):
        afstand = options['afstand']
        regio_nr = options['regio_nr']

        regiocomp = Regiocompetitie.objects.get(regio__regio_nr=regio_nr, competitie__afstand=afstand)

        for obj in (RegiocompetitieSporterBoog
                    .objects
                    .filter(regiocompetitie=regiocomp)
                    .prefetch_related('scores')
                    .order_by('sporterboog__sporter__lid_nr')):
            score_pks = obj.scores.values_list('pk', flat=True)
            print('\n', obj)
            prev_when = None
            for hist in ScoreHist.objects.filter(score__pk__in=score_pks).order_by('when'):
                if prev_when is not None:
                    interval = hist.when - prev_when
                    print('   [+%s]' % interval.days, hist)
                else:
                    print('        ', hist)
                prev_when = hist.when
        # for


# end of file
