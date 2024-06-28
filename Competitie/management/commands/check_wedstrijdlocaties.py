# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK, DEEL_RK
from Competitie.models import CompetitieMatch, Kampioenschap
from Vereniging.models import Vereniging


class Command(BaseCommand):
    help = "Check voor problemen met wedstrijdlocaties"

    def add_arguments(self, parser):
        parser.add_argument('--rk', action='store_true', help='Alleen RK checken')
        parser.add_argument('--bk', action='store_true', help='Alleen BK checken')

    def handle(self, *args, **options):

        deel = None
        if options['bk']:
            deel = DEEL_BK
        if options['rk']:
            deel = DEEL_RK

        match2deelcomp = dict()     # [wedstrijd.pk] = deelcomp

        match_pks = list()
        if deel:
            for deelkamp in Kampioenschap.objects.filter(deel=deel).prefetch_related('rk_bk_matches'):
                if deelkamp.rk_bk_matches.count() == 0:
                    self.stdout.write('[WARNING] Geen rk_bk_matches voor %s' % deelkamp)

                pks = list(deelkamp.rk_bk_matches.values_list('pk', flat=True))
                match_pks.extend(pks)

                for pk in pks:
                    match2deelcomp[pk] = deelkamp
                # for
            # for

        ver2locs = dict()   # [ver_nr] = (loc, loc, ..)

        for ver in Vereniging.objects.prefetch_related('locatie_set').all():
            ver2locs[ver.ver_nr] = locs = list()
            for loc in ver.locatie_set.exclude(zichtbaar=False):
                locs.append(loc)
            # for
        # for

        ver_gerapporteerd = list()          # [ver_nr, ..]

        matches = (CompetitieMatch
                   .objects
                   .select_related('locatie',
                                   'vereniging')
                   .prefetch_related('indiv_klassen',
                                     'team_klassen')
                   .all())
        if deel:
            matches = matches.filter(pk__in=match_pks)

        for match in matches:

            loc = match.locatie
            ver = match.vereniging
            toon_loc = False

            wed_str = 'CompetitieMatch met pk=%s' % match.pk
            if ver:
                wed_str += ' bij vereniging %s' % ver.ver_nr
                locs = ver2locs[ver.ver_nr]
            else:
                locs = list()

            klassen = list()
            for klasse in match.indiv_klassen.all():
                klassen.append(klasse.beschrijving)
            # for
            for klasse in match.team_klassen.all():
                klassen.append(klasse.beschrijving)
            # for
            if len(klassen):
                klassen_str = ", ".join(klassen)
            else:
                klassen_str = "<geen gekozen>"

            wedstrijd_fouten = list()

            if loc:
                loc_fouten = list()

                if not loc.zichtbaar:
                    loc_fouten.append('met zichtbaar=False')
                else:
                    # verwachting: banen_18m>0 of banen_25m>0; discipline_indoor = True
                    if loc.banen_18m == 0 and loc.banen_25m == 0:
                        loc_fouten.append('zonder banen 18m/25m opgaaf')
                        toon_loc = True

                    if not loc.discipline_indoor:
                        loc_fouten.append('zonder discipline_indoor')
                        toon_loc = True

                # TODO: check locatie is van juiste vereniging (laatste keer geen fouten van dit type gevonden)

                if len(loc_fouten):
                    wedstrijd_fouten.append('locatie met pk=%s %s' % (loc.pk, " en ".join(loc_fouten)))
            else:
                wedstrijd_fouten.append('geen locatie')

            if ver:
                if loc:
                    # als de gekozen locatie discipline_indoor is en banen_18m of _25m ingesteld heeft, dan is het goed
                    if (not loc.discipline_indoor) or (loc.banen_18m == 0 and loc.banen_25m == 0):
                        toon_loc = True
            else:
                wedstrijd_fouten.append('geen vereniging')
                toon_loc = False

            if len(wedstrijd_fouten) > 0:
                self.stdout.write('[ERROR] %s heeft %s' % (wed_str, " en ".join(wedstrijd_fouten)))
                try:
                    deelkamp = match2deelcomp[match.pk]
                except KeyError:
                    pass
                else:
                    self.stdout.write('        Deelcompetitie: %s' % deelkamp)

                self.stdout.write('        Wanneer: %s om %s' % (match.datum_wanneer, match.tijd_begin_wedstrijd))
                self.stdout.write('        Wedstrijdklassen: %s' % klassen_str)

            if toon_loc:
                if ver.ver_nr not in ver_gerapporteerd:     # pragma: no branch
                    ver_gerapporteerd.append(ver.ver_nr)

                    self.stdout.write('[INFO] Vereniging %s heeft %s locaties:' % (ver.pk, len(locs)))
                    for loc2 in locs:
                        if loc2.pk == loc.pk:
                            ster = '*'
                        else:
                            ster = ' '
                        self.stdout.write('       %s [pk=%s] %s' % (ster, loc2.pk, loc2))
                    # for
        # for

# end of file
