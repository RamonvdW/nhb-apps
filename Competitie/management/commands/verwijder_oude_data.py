# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdenPlan, CompetitieWedstrijdUitslag
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog

"""
    CompetitieWedstrijd + CompetitieWedstrijdUitslag
    CompetitieWedstrijdenPlan
    
    Score (type SCORE) gekoppeld aan SporterBoog zonder Sporter
    ScoreHist "Uitslag competitie seizoen 2019/2020" + Score (type SCORE) 
    ScoreHist "Uitslag competitie seizoen 2020/2021" + Score (type SCORE) 
    ScoreHist "Importeer scores van uitslagen.handboogsport.nl voor ronde".. + Score (type SCORE) 
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

    def _verwijder_score_scorehist_met_notitie(self, notitie_moet_bevatten):
        score_pks = list(ScoreHist
                         .objects
                         .filter(notitie__contains=notitie_moet_bevatten)
                         .values_list('score__pk', flat=True))
        count = len(score_pks)
        if count > 0:
            self._use_commit()
            self.stdout.write('%s records met %s' % (count, repr(notitie_moet_bevatten)))

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

    def _verwijder_orphan_wedstrijd_plan(self):
        # zoek alle plannen die niet meer aan een deelcompetitie hangen
        plans = (CompetitieWedstrijdenPlan
                 .objects
                 .prefetch_related('wedstrijden')
                 .filter(deelcompetitie=None,
                         deelcompetitieronde=None))
        plans_count = plans.count()

        wedstrijd_pks = list()
        for plan in plans:
            pks = plan.wedstrijden.values_list('pk', flat=True)
            wedstrijd_pks.extend(pks)
        # for

        weds = (CompetitieWedstrijd
                .objects
                .select_related('uitslag')
                .filter(pk__in=wedstrijd_pks))
        weds_count = weds.count()

        uitslag_pks = list()
        for wed in weds:
            if wed.uitslag:
                uitslag_pks.append(wed.uitslag.pk)
        # for

        uitslagen = (CompetitieWedstrijdUitslag
                     .objects
                     .filter(pk__in=uitslag_pks))
        uitslag_count = uitslagen.count()

        if plans_count + weds_count + uitslag_count > 0:
            self._use_commit()

        # verwijder eerst de plannen, zodat de competitiewedstrijden 'vrij' zijn
        if plans_count > 0:
            self.stdout.write('%s oude plannen' % plans_count)
            if self._do_save:
                plans.delete()

        # verwijder de wedstrijden zodat de uitslagen 'vrij' komen
        if weds_count > 0:
            self.stdout.write('%s oude wedstrijden' % weds_count)
            if self._do_save:
                weds.delete()

        if uitslag_count > 0:
            self.stdout.write('%s oude uitslagen' % uitslag_count)
            if self._do_save:
                uitslagen.delete()

    def _verwijder_orphan_wedstrijden(self):
        orphan_pks = list()
        for wed in CompetitieWedstrijd.objects.all():
            in_plans = wed.competitiewedstrijdenplan_set.all()
            count = in_plans.count()
            if count == 0:
                orphan_pks.append(wed.pk)
        # for

        if len(orphan_pks):
            self._use_commit()
            self.stdout.write('%s wedstrijden niet in een plan' % len(orphan_pks))

            orphans = CompetitieWedstrijd.objects.filter(pk__in=orphan_pks)
            if self._do_save:
                orphans.delete()

    def handle(self, *args, **options):
        self._do_save = options['commit']

        self.stdout.write('Searching..')

        """ ScoreHist.notitie bevat de opmerking
            door ScoreHist.score te verwijderen, wordt ScoreHist ook verwijderd
        """

        # al overal verwijderd
        self._verwijder_score_scorehist_met_notitie(
                    "Uitslag competitie seizoen 2019/2020")

        # behouden, want dit zijn de AG's voor seizoen 2021/2022!
        # self._verwijder_score_scorehist_met_notitie(
        #             "Uitslag competitie seizoen 2020/2021")

        self._verwijder_lege_sporterboog()

        self._verwijder_orphan_wedstrijd_plan()

        self._verwijder_orphan_wedstrijden()

        if not self._said_use_commit:
            self.stdout.write('Geen verwijderbare data gevonden')

# end of file
