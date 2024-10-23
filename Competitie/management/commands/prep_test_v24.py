# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import MUTATIE_DOORZETTEN_REGIO_NAAR_RK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMutatie,
                               Regiocompetitie, RegiocompetitieSporterBoog)
from Competitie.operations import competities_aanmaken, competitie_klassengrenzen_vaststellen
from Sporter.models import SporterBoog


class Command(BaseCommand):
    help = "Tijdelijk commando voor test-sessie v24"

    lid_nrs = (101985, 102299, 103930, 130933, 133988, 150128, 151523, 159934, 159935, 160907, 162483)

    def handle(self, *args, **options):
        comp = Competitie.objects.get(begin_jaar=2024, afstand=18)
        self.stdout.write('Competitie: %s' % comp)
        boogtypen = comp.boogtypen.all()

        for lid_nr in self.lid_nrs:
            for sb in (SporterBoog
                       .objects
                       .filter(voor_wedstrijd=True,
                               sporter__lid_nr=lid_nr,
                               boogtype__in=boogtypen)
                       .select_related('sporter',
                                       'boogtype',
                                       'sporter__bij_vereniging')):
                self.stdout.write('%s - %s' % (sb.sporter, sb.boogtype.beschrijving))

                deelnemer = (RegiocompetitieSporterBoog
                             .objects
                             .filter(sporterboog=sb,
                                     regiocompetitie__competitie=comp)
                             .select_related('regiocompetitie',
                                             'regiocompetitie__competitie',
                                             'sporterboog',
                                             'sporterboog__boogtype')
                             .first())

                if not deelnemer:
                    klasse = (CompetitieIndivKlasse
                              .objects
                              .filter(boogtype=sb.boogtype)
                              .order_by('volgorde')     # beste klasse eerst
                              .first())

                    ver = sb.sporter.bij_vereniging
                    deelcomp = Regiocompetitie.objects.filter(competitie=comp, regio=ver.regio).first()
                    if not deelcomp:
                        self.stdout.write('[ERROR] Geen regiocompetitie voor %s' % sb.sporter)
                        continue

                    deelnemer = RegiocompetitieSporterBoog(
                                    regiocompetitie=deelcomp,
                                    sporterboog=sb,
                                    bij_vereniging=ver,
                                    indiv_klasse=klasse,
                                    logboekje='Inschrijving voor test-sessie v24\n')
                    deelnemer.save()
                    self.stdout.write('Aangemaakt: %s in klasse %s' % (deelnemer, klasse))

                score = 290 - int(lid_nr % 10)

                deelnemer.score1 = score + 1
                deelnemer.score2 = score + 2
                deelnemer.score3 = score + 3
                deelnemer.score4 = score + 4
                deelnemer.score5 = score + 5
                deelnemer.score6 = score + 6
                deelnemer.score7 = score + 7
                deelnemer.totaal = 7 * score + 28
                deelnemer.aantal_scores = 7
                deelnemer.laagste_score_nr = 1
                deelnemer.gemiddelde = (score / 30) + 0.15

                # omzetten van klasse onbekend naar klasse geldig voor het RK
                klasse = (CompetitieIndivKlasse
                          .objects
                          .filter(boogtype=sb.boogtype,
                                  is_ook_voor_rk_bk=True)
                          .order_by('volgorde')     # beste klasse eerst
                          .first())
                deelnemer.indiv_klasse = klasse

                deelnemer.save()
            # for
        # for

        # geef alle sporters genoeg scores
        qset = RegiocompetitieSporterBoog.objects.filter(regiocompetitie__competitie=comp)
        self.stdout.write('Updating %s deelnemers' % qset.count())
        qset.filter(aantal_scores=1).update(score2=110, aantal_scores=2)
        qset.filter(aantal_scores=2).update(score3=120, aantal_scores=3)
        qset.filter(aantal_scores=3).update(score4=130, aantal_scores=4)
        qset.filter(aantal_scores=4).update(score5=140, aantal_scores=5)
        qset.filter(aantal_scores=5).update(score6=150, aantal_scores=6)

        self.stdout.write('Regios afsluiten')
        Regiocompetitie.objects.filter(competitie=comp, is_afgesloten=False).update(is_afgesloten=True)

        self.stdout.write('Doorzetten naar RK')
        CompetitieMutatie(mutatie=MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                          door='prep_test_v24',
                          competitie=comp).save()

        self.stdout.write('Competitie 2025 aanmaken')
        Competitie.objects.filter(begin_jaar=2025).delete()
        competities_aanmaken(jaar=2025)
        for comp in Competitie.objects.filter(begin_jaar=2025):
            competitie_klassengrenzen_vaststellen(comp)

            comp.refresh_from_db()
            comp.begin_fase_C = '2024-10-20'            # inschrijving open
            comp.begin_fase_D_indiv = '2024-11-20'
            comp.save()
        # for

# end of file
