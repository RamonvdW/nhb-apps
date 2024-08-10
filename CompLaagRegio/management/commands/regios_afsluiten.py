# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, Regiocompetitie


class Command(BaseCommand):
    help = "Sluit alle regiocompetities van een specifieke competitie"

    def _sluit_regios(self, comp, regio_van, regio_tot):
        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('regio')
                         .filter(competitie=comp,
                                 is_afgesloten=False)
                         .order_by('regio__regio_nr')):

            regio_nr = deelcomp.regio.regio_nr
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

        # in geval van meerdere competities, pak de oudste (laagste begin_jaar)
        comps = (Competitie
                 .objects
                 .filter(afstand=afstand,
                         is_afgesloten=False)
                 .order_by('begin_jaar'))

        if len(comps) == 0:
            self.stderr.write('[ERROR] Kan competitie met afstand %s niet vinden' % afstand)
            return

        comp = comps[0]
        comp.bepaal_fase()
        if comp.fase_indiv < 'F' or comp.fase_indiv > 'G':
            self.stderr.write('[ERROR] Competitie in fase_indiv %s is niet ondersteund' % comp.fase_indiv)
            return

        self._sluit_regios(comp, regio_van, regio_tot)

# end of file
