# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_RK
from Competitie.models import Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam


class Command(BaseCommand):
    help = "Check download van de RK formulieren"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'),
                            help='Competitie afstand (18/25)')
        parser.add_argument('type', type=str, choices=('indiv', 'teams'))

    def handle(self, *args, **options):

        afstand = options['afstand']
        klasse_type = options['type']

        for deelkamp in (Kampioenschap
                         .objects
                         .filter(competitie__afstand=afstand,
                                 deel=DEEL_RK)
                         .select_related('rayon',
                                         'competitie')
                         .prefetch_related('rk_bk_matches')
                         .order_by('rayon__rayon_nr')):

            # skip volgende seizoen
            comp = deelkamp.competitie
            comp.bepaal_fase()
            if comp.fase_indiv < 'E':
                # skip nieuwe competitie in regio fase
                continue

            if deelkamp.rayon.rayon_nr == 1:
                self.stdout.write('Competitie: %s' % deelkamp.competitie)

            self.stdout.write('\n%s' % deelkamp)

            indiv_matches = list()
            team_matches = list()

            # check elke match voor dit RK
            for match in (deelkamp
                          .rk_bk_matches
                          .exclude(vereniging=None)
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .order_by('datum_wanneer',
                                    'vereniging')):

                for klasse in match.indiv_klassen.all():
                    tup = (match, klasse)
                    indiv_matches.append(tup)
                # for

                for klasse in match.team_klassen.all():
                    tup = (match, klasse)
                    team_matches.append(tup)
                # for
            # for

            if klasse_type == 'indiv':
                for match, klasse in indiv_matches:
                    kort = klasse.beschrijving.replace(' klasse ', ' kl')
                    kort = kort.replace(klasse.boogtype.beschrijving, klasse.boogtype.afkorting)
                    kort = kort.replace('Onder ', 'O')
                    kort = kort.replace('Jeugd', 'jeugd')
                    kort = kort.replace(' ', '_')

                    count = KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp, indiv_klasse=klasse).count()

                    self.stdout.write(
                        '%s %s %s %s %s' % (
                            match.datum_wanneer,
                            match.vereniging.ver_nr,
                            '%s/%s' % (match.pk, klasse.pk),
                            count,
                            kort))
                # for

            if klasse_type == 'teams':
                for match, klasse in team_matches:
                    kort = klasse.beschrijving.replace(' klasse ', ' ')
                    kort = kort.replace('Recurve', 'R')
                    kort = kort.replace('Compound', 'C')
                    kort = kort.replace('Barebow', 'BB')
                    kort = kort.replace('Longbow', 'LB')
                    kort = kort.replace('Traditional', 'TR')
                    kort = kort.replace(' ', '_')

                    count = KampioenschapTeam.objects.filter(kampioenschap=deelkamp, team_klasse=klasse).count()

                    self.stdout.write(
                        '%s %s %s %s %s' % (
                            match.datum_wanneer,
                            match.vereniging.ver_nr,
                            '%s/%s' % (match.pk, klasse.pk),
                            count,
                            kort))
                # for

        # for

# end of file
