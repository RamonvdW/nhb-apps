# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK
from CompKampioenschap.operations import ImporteerUitslagTeamsExcel


class Command(BaseCommand):

    help = "Importeer uitslag BK Teams"

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'), help='Competitie afstand (18/25)')
        parser.add_argument('bestand', type=str, help='Pad naar het Excel bestand')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('--dryrun', action='store_true')

    def handle(self, *args, **options):
        dryrun = options['dryrun']
        verbose = options['verbose']
        afstand = options['afstand']
        fname = options['bestand']

        importeer = ImporteerUitslagTeamsExcel(self.stdout, self.stderr, dryrun, verbose, afstand, DEEL_BK)
        importeer.importeer_bestand(fname)

# end of file
