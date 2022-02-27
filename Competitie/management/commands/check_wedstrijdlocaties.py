# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Competitie.models import DeelCompetitie, LAAG_BK, LAAG_RK
from NhbStructuur.models import NhbVereniging
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdenPlan


class Command(BaseCommand):
    help = "Check voor problemen met wedstrijdlocaties"

    def add_arguments(self, parser):
        parser.add_argument('--rk', action='store_true', help='Alleen RK checken')
        parser.add_argument('--bk', action='store_true', help='Alleen BK checken')

    def handle(self, *args, **options):

        laag = None
        if options['bk']:
            laag = LAAG_BK
        if options['rk']:
            laag = LAAG_RK

        wedstrijd2deelcomp = dict()     # [wedstrijd.pk] = deelcomp

        wedstrijd_pks = list()
        if laag:
            for deelcomp in DeelCompetitie.objects.filter(laag=laag).select_related('plan'):
                if deelcomp.plan:
                    if deelcomp.plan.wedstrijden.count() == 0:
                        self.stdout.write('[WARNING] Geen wedstrijden voor deelcompetitie %s' % deelcomp)

                    pks = list(deelcomp.plan.wedstrijden.values_list('pk', flat=True))
                    wedstrijd_pks.extend(pks)

                    for pk in pks:
                        wedstrijd2deelcomp[pk] = deelcomp
                    # for
                else:
                    self.stdout.write('[WARNING] Geen plan of wedstrijden voor deelcompetitie %s' % deelcomp)

        ver2locs = dict()   # [ver_nr] = (loc, loc, ..)

        for ver in NhbVereniging.objects.prefetch_related('wedstrijdlocatie_set').all():
            ver2locs[ver.ver_nr] = locs = list()
            for loc in ver.wedstrijdlocatie_set.exclude(zichtbaar=False):
                locs.append(loc)
            # for
        # for

        ver_gerapporteerd = list()          # [ver_nr, ..]

        wedstrijden = CompetitieWedstrijd.objects.select_related('locatie', 'vereniging').prefetch_related('indiv_klassen', 'team_klassen').all()
        if laag:
            wedstrijden = wedstrijden.filter(pk__in=wedstrijd_pks)

        for wedstrijd in wedstrijden:

            loc = wedstrijd.locatie
            ver = wedstrijd.vereniging
            toon_loc = False

            wed_str = 'CompetitieWedstrijd met pk=%s' % wedstrijd.pk
            if ver:
                wed_str += ' bij vereniging %s' % ver.ver_nr
                locs = ver2locs[ver.ver_nr]
            else:
                locs = list()

            klassen = list()
            for klasse in wedstrijd.indiv_klassen.all():
                klassen.append(klasse.beschrijving)
            # for
            for klasse in wedstrijd.team_klassen.all():
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
                # kijk hoeveel wedstrijdlocaties deze vereniging heeft
                if len(locs) > 1:
                    # als de gekozen locatie discipline_indoor is en banen_18m/banen_25m ingesteld heeft, dan is het goed
                    if (not loc.discipline_indoor) or (loc.banen_18m == 0 and loc.banen_25m == 0):
                        toon_loc = True
            else:
                wedstrijd_fouten.append('geen vereniging')
                toon_loc = False

            if len(wedstrijd_fouten) > 0:
                self.stdout.write('[ERROR] %s heeft %s' % (wed_str, " en ".join(wedstrijd_fouten)))
                try:
                    deelcomp = wedstrijd2deelcomp[wedstrijd.pk]
                except KeyError:
                    pass
                else:
                    self.stdout.write('        Deelcompetitie: %s' % deelcomp)

                self.stdout.write('        Wanneer: %s om %s' % (wedstrijd.datum_wanneer, wedstrijd.tijd_begin_wedstrijd))
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
