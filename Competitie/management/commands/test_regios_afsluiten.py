# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, DeelCompetitie, LAAG_REGIO


class Command(BaseCommand):
    help = "Sluit alle regiocompetities van een specifieke competitie"

    def _sluit_regios(self, comp, regio_van, regio_tot):
        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('nhb_regio')
                         .filter(competitie=comp,
                                 is_afgesloten=False,
                                 laag=LAAG_REGIO)
                         .order_by('nhb_regio__regio_nr')):

            if not deelcomp.is_afgesloten:
                regio_nr = deelcomp.nhb_regio.regio_nr
                if regio_van <= regio_nr <= regio_tot:
                    self.stdout.write('[INFO] Deelcompetitie %s wordt afgesloten' % deelcomp)
                    deelcomp.is_afgesloten = True
                    deelcomp.save()
        # for

    def add_arguments(self, parser):
        parser.add_argument('afstand', nargs=1, help="Competitie afstand (18 of 25)")
        parser.add_argument('regio_van', nargs=1, help="Eerste regio om af te sluiten")
        parser.add_argument('regio_tot', nargs=1, help="Laatste regio om af te sluiten")

    def handle(self, *args, **options):
        afstand = options['afstand'][0]

        try:
            regio_van = int(options['regio_van'][0])
            regio_tot = int(options['regio_tot'][0])
        except ValueError:
            self.stderr.write('[ERROR] Valide regio nummers: 101 tot 116')
            return

        if regio_van < 101 or regio_tot < 101 or regio_van > 116 or regio_tot > 116 or regio_van > regio_tot:
            self.stderr.write('[ERROR] Valide regio nummers: 101 tot 116, oplopend')
            return

        try:
            # in geval van meerdere competities, pak de oudste (laagste begin_jaar)
            comp = (Competitie
                    .objects
                    .filter(afstand=afstand,
                            is_afgesloten=False)
                    .order_by('begin_jaar'))[0]
        except Competitie.DoesNotExist:
            self.stderr.write('[ERROR] Kan competitie met afstand %s niet vinden' % afstand)
            return

        comp.zet_fase()
        if comp.fase < 'F' or comp.fase > 'G':
            self.stderr.write('[ERROR] Competitie in fase %s is niet ondersteund' % comp.fase)
            return

        self._sluit_regios(comp, regio_van, regio_tot)

# end of file
