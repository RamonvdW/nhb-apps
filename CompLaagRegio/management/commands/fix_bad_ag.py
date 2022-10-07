# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, RegioCompetitieSchutterBoog, AG_NUL
from Competitie.operations.klassengrenzen import KlasseBepaler
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist, AG_DOEL_INDIV, AG_DOEL_TEAM
from Sporter.models import SporterVoorkeuren


class Command(BaseCommand):
    help = "Controleer en corrigeer AG foutjes"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Voorgestelde wijzigingen opslaan')
        parser.add_argument('afstand', type=int, help='Competitie afstand (18/25)')

    def handle(self, *args, **options):

        afstand = options['afstand']

        # pak de jongste competitie
        comps = Competitie.objects.filter(is_afgesloten=False, afstand=afstand).order_by('-begin_jaar')  # jongste eerst
        if len(comps) == 0:
            self.stderr.write('[ERROR] Geen actieve competitie gevonden')
            return

        comp = comps[0]
        self.stdout.write('[INFO] Gekozen competitie: %s' % comp)

        comp.bepaal_fase()
        self.stdout.write('[INFO] Fase: %s' % comp.fase)

        if not ('B' <= comp.fase <= 'E'):
            self.stderr.write('[ERROR] Competitie is in de verkeerde fase')
            return

        bepaler = KlasseBepaler(comp)
        vertel_commit = False

        sporterboog_pk2ag_indiv = dict()
        for ag in (Aanvangsgemiddelde
                   .objects
                   .select_related('sporterboog')
                   .filter(doel=AG_DOEL_INDIV,
                           afstand_meter=afstand)):
            sporterboog_pk2ag_indiv[ag.sporterboog.pk] = ag.waarde
        # for

        sporterboog_pk2ag_teams = dict()
        for ag_hist in (AanvangsgemiddeldeHist
                        .objects
                        .select_related('ag',
                                        'ag__sporterboog')
                        .filter(ag__doel=AG_DOEL_TEAM,
                                ag__afstand_meter=afstand)
                        .order_by('-when')):
            ag = ag_hist.ag
            # alleen het eerste (nieuwste) AG gebruiken
            if ag.sporterboog.pk not in sporterboog_pk2ag_teams:
                sporterboog_pk2ag_teams[ag.sporterboog.pk] = ag.waarde
        # for

        sporter_pk2wedstrijdgeslacht = dict()
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            if voorkeuren.wedstrijd_geslacht_gekozen:
                wedstrijdgeslacht = voorkeuren.wedstrijd_geslacht   # M/V
            else:
                wedstrijdgeslacht = voorkeuren.sporter.geslacht     # M/V/X
            sporter_pk2wedstrijdgeslacht[voorkeuren.sporter.pk] = wedstrijdgeslacht
        # for

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'indiv_klasse')
                          .filter(deelcompetitie__competitie=comp)):

            try:
                ag_indiv = sporterboog_pk2ag_indiv[deelnemer.sporterboog.pk]
            except KeyError:
                ag_indiv = AG_NUL

            try:
                ag_teams = sporterboog_pk2ag_teams[deelnemer.sporterboog.pk]
            except KeyError:
                ag_teams = ag_indiv

            ag_indiv_str = "%.3f" % ag_indiv
            ag_teams_str = "%.3f" % ag_teams

            do_save = False

            if ag_teams_str != str(deelnemer.ag_voor_team):
                self.stdout.write('deelnemer %s : AG team %s --> %s' % (deelnemer, deelnemer.ag_voor_team, ag_teams_str))
                deelnemer.ag_voor_team = ag_teams
                do_save = True

            if ag_indiv_str != str(deelnemer.ag_voor_indiv):
                self.stdout.write('deelnemer %s : AG indiv %s --> %s' % (deelnemer, deelnemer.ag_voor_indiv, ag_indiv_str))
                deelnemer.ag_voor_indiv = ag_indiv
                do_save = True

                try:
                    wedstrijdgeslacht = sporter_pk2wedstrijdgeslacht[deelnemer.sporterboog.sporter.pk]
                except KeyError:
                    wedstrijdgeslacht = deelnemer.sporterboog.sporter.geslacht

                # klasse opnieuw bepalen
                indiv_klasse = deelnemer.indiv_klasse
                bepaler.bepaal_klasse_deelnemer(deelnemer, wedstrijdgeslacht)

                if indiv_klasse != deelnemer.indiv_klasse:
                    self.stdout.write('deelnemer %s : indiv_klasse=%s --> %s' % (
                                        deelnemer, indiv_klasse, deelnemer.indiv_klasse))
                    do_save = True

            if do_save:
                if options['commit']:
                    deelnemer.save()
                else:
                    vertel_commit = True
        # for

        if vertel_commit:
            self.stdout.write('\nGebruik --commit om wijzigingen door te voeren')

# end of file
