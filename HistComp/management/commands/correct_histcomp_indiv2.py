# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# corrigeer de HistCompetitieIndividueel records: gemiddelde

from django.core.management.base import BaseCommand
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from decimal import Decimal


class Command(BaseCommand):
    help = "Corrigeer historische competitie uitslag, individueel"

    def _corrigeer(self, histcomp, aantal_pijlen):

        aantal_gemiddelden = 0
        aantal_rank = 0
        te_verwijderen_pks = list()
        verwacht_laatste = False

        tups = list()
        for obj in (HistCompetitieIndividueel
                    .objects
                    .filter(histcompetitie=histcomp)
                    .order_by('rank')):

            alle_scores = [obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7]

            scores = [score for score in alle_scores if score > 0]
            scores.sort(reverse=True)       # hoogste eerst

            aantal = min(len(scores), histcomp.aantal_beste_scores)
            scores = scores[:aantal]

            if aantal == 0:
                te_verwijderen_pks.append(obj.pk)
                verwacht_laatste = True
            else:
                if verwacht_laatste:
                    self.stderr.write('[ERROR] Onverwacht: uitslag na rank zonder scores')
                    return

                totaal = sum(scores)
                gemiddelde = Decimal(totaal)
                gemiddelde /= aantal
                gemiddelde /= aantal_pijlen
                gemiddelde = round(gemiddelde, 3)

                diff = abs(obj.gemiddelde - gemiddelde)
                if diff >= 0.001:
                    obj.gemiddelde = gemiddelde
                    obj.save(update_fields=['gemiddelde'])
                    aantal_gemiddelden += 1

                tup = (aantal, gemiddelde, obj.pk, obj)
                tups.append(tup)
        # for

        tups.sort(reverse=True)     # hoogste aantal en gemiddelde eerst

        rank = 1
        for _, _, _, obj in tups:
            if rank != obj.rank:
                obj.rank = rank
                obj.save(update_fields=['rank'])
                aantal_rank += 1
            rank += 1
        # for

        if aantal_gemiddelden > 0:
            self.stdout.write('[INFO] %s gemiddelden aangepast' % aantal_gemiddelden)

        if aantal_rank > 0:
            self.stdout.write('[INFO] %s rank aangepast' % aantal_rank)

        if len(te_verwijderen_pks) > 0:
            HistCompetitieIndividueel.objects.filter(pk__in=te_verwijderen_pks).delete()
            self.stdout.write('[INFO] %s uitslagen zonder scores verwijderd' % len(te_verwijderen_pks))

    def handle(self, *args, **options):
        for histcomp in HistCompetitie.objects.all().order_by('seizoen', 'comp_type'):
            self.stdout.write('[INFO] Corrigeer %s - %sm - %s' % (histcomp.seizoen, histcomp.comp_type, histcomp.boog_str))
            aantal_pijlen = 30 if histcomp.comp_type == '18' else 25
            self._corrigeer(histcomp, aantal_pijlen)
        # for

# end of file
