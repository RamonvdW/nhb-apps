# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieSporterBoog
from Sporter.models import SporterBoog


class Command(BaseCommand):
    help = "Rapporteer afwijkingen tussen de inschrijvingen en huidige voorkeuren van elke sporter"

    @staticmethod
    def afkappen(msg, limiet):
        lengte = len(msg)
        if lengte > limiet:
            msg = msg[:limiet-2]
            if msg[-1] == ' ':
                msg = msg[:-1]
            msg += '..'
        return msg

    def handle(self, *args, **options):

        self.stdout.write('Deelnemers met ingeschreven boogtype niet meer actief als wedstrijdboog')
        # zoek alle leden met een andere voorkeur dan ingeschreven
        prev_comp = None
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .exclude(sporterboog__boogtype__afkorting='C')        # kan toch niet overzetten
                          .filter(sporterboog__voor_wedstrijd=False,
                                  aantal_scores__gte=1)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'regiocompetitie')
                          .order_by('regiocompetitie',
                                    'bij_vereniging',
                                    'sporterboog__sporter__lid_nr')):

            deelcomp = deelnemer.regiocompetitie
            if deelcomp.competitie != prev_comp:
                prev_comp = deelcomp.competitie
                self.stdout.write('\n%s:' % prev_comp)

            sporter = deelnemer.sporterboog.sporter
            voorkeuren = (SporterBoog
                          .objects
                          .filter(sporter=sporter,
                                  voor_wedstrijd=True)
                          .select_related('boogtype')
                          .values_list('boogtype__afkorting',
                                       flat=True))
            wil_str = ", ".join(list(voorkeuren))
            if not wil_str:
                wil_str = '?'
            self.stdout.write('Regio %s   %-30s   %-30s   %-2s -> %s' % (
                            deelcomp.regio.regio_nr,
                            self.afkappen(str(deelnemer.bij_vereniging), 30),
                            self.afkappen(sporter.lid_nr_en_volledige_naam(), 40),
                            deelnemer.sporterboog.boogtype.afkorting,
                            wil_str))
        # for

# end of file
