# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from HistComp.models import HistCompRegioIndiv


class Command(BaseCommand):         # pragma: no cover
    help = "Check consistentie van historische uitslag, individueel"

    def add_arguments(self, parser):
        parser.add_argument('seizoen', nargs=1,
                            help="competitie seizoen: 20xx/20yy")
        parser.add_argument('comptype', nargs=1, choices=('18', '25'),
                            help="competitie type: 18 of 25")

    def handle(self, *args, **options):
        # self.stderr.write("import individuele competitie historie. args=%s, options=%s" % (repr(args), repr(options)))
        comp_type = options['comptype'][0]
        seizoen = options['seizoen'][0]

        prev_histcomp_pk = -1
        prev_rank = 0
        prev_gem = 0
        for obj in (HistCompRegioIndiv
                    .objects
                    .filter(histcompetitie__seizoen=seizoen,
                            histcompetitie__comp_type=comp_type)
                    .select_related('histcompetitie')
                    .order_by('histcompetitie__boog_str',
                              'rank')):

            if obj.histcompetitie.pk != prev_histcomp_pk:
                self.stdout.write('\n[INFO] %s, %s' % (obj.histcompetitie.seizoen, obj.histcompetitie.beschrijving))
                prev_histcomp_pk = obj.histcompetitie.pk
                prev_rank = 0
                prev_gem = 0

            if prev_rank:
                if obj.rank != prev_rank + 1:
                    self.stdout.write('[WARNING] obj pk=%s met gem=%s, rank=%s niet opvolgend (prev: gem=%s, rank=%s)' % (obj.pk, obj.gemiddelde, obj.rank, prev_gem, prev_rank))
            prev_rank = obj.rank
            prev_gem = obj.gemiddelde
        # for

# end of file
