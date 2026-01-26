# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_RK, DEELNAME_NEE
from Competitie.models import CompetitieIndivKlasse, Kampioenschap, KampioenschapSporterBoog


class Command(BaseCommand):

    help = "Controleer de RK uitslagen"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'),
                            help='Competitie afstand (18/25)')
        parser.add_argument('--verbose', action='store_true')

    def handle(self, *args, **options):

        afstand = options['afstand']
        verbose = options['verbose']

        for deelkamp in (Kampioenschap
                         .objects
                         .filter(competitie__afstand=afstand,
                                 deel=DEEL_RK)
                         .order_by('rayon__rayon_nr')):

            self.stdout.write('[INFO] %s' % deelkamp)

            # check elke klasse voor een uitslag
            for wkl in (CompetitieIndivKlasse
                        .objects
                        .filter(is_ook_voor_rk_bk=True,
                                competitie=deelkamp.competitie)
                        .order_by('volgorde')):

                kampioenen = (KampioenschapSporterBoog
                              .objects
                              .filter(kampioenschap=deelkamp,
                                      indiv_klasse=wkl)
                              .exclude(deelname=DEELNAME_NEE))
                heeft_kampioen = 1 == kampioenen.filter(result_rank=1).count()
                aantal = kampioenen.count()

                if verbose:
                    self.stdout.write('[INFO] %2d deelnemers in %s' % (aantal, wkl.beschrijving))

                if not heeft_kampioen and aantal > 0:
                    self.stdout.write('[WARNING] Klasse %s met %s deelnemers heeft geen kampioen' % (
                        wkl.beschrijving, aantal))

                # controleer de volgorde van de ranking
                nr = 0
                for kampioen in (KampioenschapSporterBoog
                                 .objects
                                 .filter(kampioenschap=deelkamp,
                                         indiv_klasse=wkl)
                                 .exclude(deelname=DEELNAME_NEE)
                                 .exclude(result_rank__gte=100)
                                 .order_by('result_volgorde')):

                    nr += 1
                    rank = kampioen.result_rank
                    volgorde = kampioen.result_volgorde

                    if verbose:
                        self.stdout.write('[DEBUG] nr=%s, rank=%s, volgorde=%s' % (nr, rank, volgorde))

                    if nr != volgorde:
                        self.stdout.write('[WARNING] Onverwachte result_volgorde: %s voor deelnemer %s' % (
                                            volgorde, kampioen))

                    if nr == 1:
                        check_rank = (1,)
                    elif nr == 2:
                        check_rank = (2,)
                    elif nr == 3:
                        check_rank = (3,)
                    elif nr == 4:
                        check_rank = (3, 4)     # 3 als er geen bronzen finale geschoten is
                    elif nr in (5, 6, 7, 8):
                        check_rank = (5,)
                    elif 9 <= nr <= 16:
                        check_rank = (9, nr)
                    else:
                        check_rank = (nr,)

                    if rank not in check_rank:
                        self.stdout.write(
                            '[WARNING] Onverwachte result_rank: %s (verwacht: %s) voor deelnemer %s in klasse %s' % (
                                rank, "/".join([str(rank) for rank in check_rank]), kampioen, kampioen.indiv_klasse))
                # for
            # for
        # for

# end of file
