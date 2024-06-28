# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Competitie.models import CompetitieMatch
from Score.definities import SCORE_TYPE_GEEN
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog

"""
    CompetitieMatch + Uitslag

    Surrogaat scores (type "geen score") die ingezet zijn voor de team competitie    
    Score (type SCORE) gekoppeld aan SporterBoog zonder Sporter
    # ScoreHist "Uitslag competitie seizoen 2021/2022" + Score (type SCORE)     --> pas op, dit is AG!
    ScoreHist "Nieuw handmatig AG voor teams"
    ScoreHist "Invoer uitslag wedstrijd"
    Wedstrijden die niet in een plan zitten
"""

DELETE_BLOCK_SIZE = 500


class Command(BaseCommand):
    help = "Verwijder oude data (scores, wedstrijden)"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self._said_use_commit = False
        self._do_save = False

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true')

    def _use_commit(self):
        if not self._said_use_commit:
            if not self._do_save:
                self.stderr.write('Let op: gebruik --commit om de voorstellen echt te verwijderen')
            self._said_use_commit = True

    def _verwijder_geen_score(self):
        scores = Score.objects.filter(type=SCORE_TYPE_GEEN)
        count = scores.count()
        if count > 0:
            self._use_commit()
            self.stdout.write('%s Score type "geen score"' % count)

            if self._do_save:
                scores.delete()

    def _verwijder_score_scorehist_met_notitie(self, notitie_moet_bevatten):
        score_pks = list(ScoreHist
                         .objects
                         .filter(notitie__contains=notitie_moet_bevatten)
                         .values_list('score__pk', flat=True))
        count = len(score_pks)
        if count > 0:
            self._use_commit()
            self.stdout.write('%s ScoreHist met %s' % (count, repr(notitie_moet_bevatten)))

            # verwijder in blokken om geen overflow te veroorzaken
            while len(score_pks):
                if len(score_pks) > DELETE_BLOCK_SIZE:
                    blok = score_pks[:DELETE_BLOCK_SIZE]
                    score_pks = score_pks[DELETE_BLOCK_SIZE:]
                else:
                    blok = score_pks
                    score_pks = list()

                if self._do_save:
                    Score.objects.filter(pk__in=blok).delete()
            # while

    def _verwijder_lege_sporterboog(self):
        sporters = SporterBoog.objects.filter(sporter=None)
        count = sporters.count()
        if count > 0:
            self._use_commit()
            self.stdout.write('%s sporterboog zonder sporter' % count)

            scores = Score.objects.filter(sporterboog__in=sporters)
            count2 = scores.count()
            if count2 > 0:
                self.stdout.write('%s scores van sporterboog zonder sporter' % count2)
                if self._do_save:
                    scores.delete()

            if self._do_save:
                sporters.delete()

    def _verwijder_lege_score(self):
        # verwijder score zonder SporterBoog
        scores = Score.objects.filter(sporterboog=None)
        count = scores.count()
        if count > 0:
            self._use_commit()
            self.stdout.write('%s Score zonder SporterBoog' % count)

            if self._do_save:
                scores.delete()

    def _verwijder_orphan_matches(self):
        orphan_pks = list()
        for match in CompetitieMatch.objects.all():
            in_plans1 = match.kampioenschap_set.all()
            in_plans2 = match.regiocompetitieronde_set.all()
            count = in_plans1.count() + in_plans2.count()
            if count == 0:
                orphan_pks.append(match.pk)
        # for

        if len(orphan_pks):
            self._use_commit()
            self.stdout.write('%s wedstrijden (CompetitieMatch) niet in een regiocompetitie of ronde' % len(orphan_pks))

            orphans = CompetitieMatch.objects.filter(pk__in=orphan_pks)
            if self._do_save:
                orphans.delete()

    def handle(self, *args, **options):
        self._do_save = options['commit']

        self.stdout.write('Searching..')

        """ ScoreHist.notitie bevat de opmerking
            door ScoreHist.score te verwijderen, wordt ScoreHist ook verwijderd
        """

        self._verwijder_geen_score()

        # behouden, want dit zijn de AG's voor seizoen 2022/2023!
        # self._verwijder_score_scorehist_met_notitie("Uitslag competitie seizoen 2021/2022")

        self._verwijder_score_scorehist_met_notitie("Invoer uitslag wedstrijd")

        # behouden, want dit kan zijn voor seizoen 2023/2024!
        # self._verwijder_score_scorehist_met_notitie("Nieuw handmatig AG voor teams")

        # behouden, want dit zijn de AG's voor seizoen 2021/2022!
        # self._verwijder_score_scorehist_met_notitie(
        #             "Uitslag competitie seizoen 2021/2022")

        self._verwijder_lege_sporterboog()

        self._verwijder_lege_score()

        self._verwijder_orphan_matches()

        if not self._said_use_commit:
            self.stdout.write('Geen verwijderbare data gevonden')

# end of file
