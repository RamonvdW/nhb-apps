# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, RegioCompetitieSchutterBoog, AG_NUL
from Competitie.operations.klassengrenzen import KlasseBepaler
from Score.models import Aanvangsgemiddelde, AG_DOEL_INDIV
from decimal import Decimal


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

        sporterboog_pk2ag = dict()
        for ag in (Aanvangsgemiddelde
                   .objects
                   .select_related('sporterboog')
                   .filter(doel=AG_DOEL_INDIV,
                           afstand_meter=afstand)):
            sporterboog_pk2ag[ag.sporterboog.pk] = ag.waarde
        # for

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'indiv_klasse')
                          .filter(deelcompetitie__competitie=comp)):

            try:
                ag = sporterboog_pk2ag[deelnemer.sporterboog.pk]
            except KeyError:
                ag = AG_NUL

            ag_str = "%.3f" % ag

            do_save = False

            if ag_str != str(deelnemer.ag_voor_team):
                self.stdout.write('deelnemer %s : AG team %s --> %s' % (deelnemer, deelnemer.ag_voor_team, ag_str))
                deelnemer.ag_voor_team = ag
                do_save = True

            if ag_str != str(deelnemer.ag_voor_indiv):
                self.stdout.write('deelnemer %s : AG indiv %s --> %s' % (deelnemer, deelnemer.ag_voor_indiv, ag_str))
                deelnemer.ag_voor_indiv = ag
                do_save = True

                # klasse opnieuw bepalen
                indiv_klasse = deelnemer.indiv_klasse
                bepaler.bepaal_klasse_deelnemer(deelnemer)

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
