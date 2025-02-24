# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Regiocompetitie, RegiocompetitieRonde, CompetitieMatch
import csv


CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


class Command(BaseCommand):
    help = "Toon aantal ingevoerde scores voor elke regiocompetitie wedstrijd in een regio"

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=int, help='Competitie afstand (18 of 25)', choices={18, 25})
        parser.add_argument('regio_nr', type=int, help='Regio nummer (101..116)', choices={*range(101, 116+1)})
        parser.add_argument('out_fname', type=str, help='Output filename')

    def handle(self, *args, **options):
        afstand = options['afstand']
        regio_nr = options['regio_nr']
        out_fname = options['out_fname']

        regiocomp = Regiocompetitie.objects.get(regio__regio_nr=regio_nr, competitie__afstand=afstand)

        pks = list()
        for pk in (RegiocompetitieRonde
                   .objects
                   .filter(regiocompetitie=regiocomp)
                   .prefetch_related('matches')
                   .values_list('matches__pk', flat=True)):
            pks.append(pk)
        # for

        with open(out_fname, 'w') as f:
            writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(['Datum', 'Tijdstip', 'ver_nr', 'Vereniging', 'Aantal ingevoerde sores'])

            totaal = 0
            for match in (CompetitieMatch
                          .objects.filter(pk__in=pks)
                          .exclude(uitslag=None)
                          .order_by('datum_wanneer',
                                    'tijd_begin_wedstrijd',
                                    'vereniging')):
                count = match.uitslag.scores.count()
                totaal += count

                row = [match.datum_wanneer, str(match.tijd_begin_wedstrijd)[:5],
                       match.vereniging.ver_nr, match.vereniging.naam,
                       count]
                writer.writerow(row)
            # for

        self.stdout.write('totaal aantal ingevoerde scores in regio %s: %s' % (regio_nr, totaal))

# end of file
