# -*- coding: utf-8 -*-

#  Copyright (c) 20202021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, RegioCompetitieSchutterBoog
from Competitie.operations.klassegrenzen import KlasseBepaler
from Score.models import Score, SCORE_TYPE_INDIV_AG


class Command(BaseCommand):
    help = "Controleer en corrigeer AG foutjes"

    def handle(self, *args, **options):

        afstand = 18
        comp = Competitie.objects.get(afstand=afstand)
        bepaler = KlasseBepaler(comp)

        for deelnemer in RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__competitie=comp):

            try:
                score = Score.objects.get(schutterboog=deelnemer.schutterboog,
                                          type=SCORE_TYPE_INDIV_AG,
                                          afstand_meter=afstand)
                ag = score.waarde / 1000.0
            except Score.DoesNotExist:
                ag = 0.0

            ag_str = "%.3f" % ag

            if ag_str != str(deelnemer.ag_voor_indiv):
                print('deelnemer %s : AG %s --> %s' % (deelnemer, deelnemer.ag_voor_indiv, ag_str))
                do_save = True

                klasse = deelnemer.klasse

                deelnemer.ag_voor_indiv = ag
                deelnemer.ag_voor_teams = ag

                bepaler.bepaal_klasse_deelnemer(deelnemer)

                if klasse != deelnemer.klasse:
                    print('deelnemer %s : klasse=%s --> %s' % (deelnemer, klasse, deelnemer.klasse))
                    do_save = True

                if do_save:
                    deelnemer.save()
        # for

# end of file
