# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import DeelKampioenschap, KampioenschapSporterBoog


class Command(BaseCommand):
    help = "Importeer uitslag kampioenschap"

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'),
                            help='Competitie afstand (18/25)')
        parser.add_argument('rayon', type=int, choices=range(1, 4+1),
                            help='rayon nummer (1..4)')

    def handle(self, *args, **options):

        afstand = options['afstand']
        rayon_nr = options['rayon']

        kampioenschap = DeelKampioenschap.objects.get(competitie__afstand=afstand, nhb_rayon__rayon_nr=rayon_nr)

        sporterboog_pks = list()
        prev_klasse = -1
        for kampioen in (KampioenschapSporterBoog
                         .objects
                         .filter(kampioenschap=kampioenschap)
                         .select_related('sporterboog',
                                         'sporterboog__sporter')
                         .order_by('indiv_klasse__volgorde',
                                   'volgorde',
                                   '-gemiddelde')):

            if kampioen.indiv_klasse.volgorde != prev_klasse:
                prev_klasse = kampioen.indiv_klasse.volgorde
                prev_volgorde = 0
                prev_rank = 0
                self.stdout.write('\n[INFO] Indiv klasse: %s ----------------------------' % kampioen.indiv_klasse)

            self.stdout.write('[INFO] rank %2d, volgorde %3d, gem=%.3f, deelname=%s, sporterboog %s' % (
                                kampioen.rank, kampioen.volgorde, kampioen.gemiddelde, kampioen.deelname, kampioen.sporterboog))

            if kampioen.sporterboog.pk not in sporterboog_pks:
                sporterboog_pks.append(kampioen.sporterboog.pk)
            else:
                self.stderr.write('[ERROR] Dubbele sporterboog!!')

            if prev_volgorde:
                if kampioen.volgorde != prev_volgorde + 1:
                    self.stdout.write('[WARNING] Volgorde niet consecutief (pk=%s)' % kampioen.pk)
            prev_volgorde = kampioen.volgorde

            if kampioen.rank != 0:
                if prev_rank:
                    if kampioen.rank != prev_rank + 1:
                        self.stderr.write('[ERROR] Rank niet consecutief (pk=%s)' % kampioen.pk)
                prev_rank = kampioen.rank
        # for

# end of file
