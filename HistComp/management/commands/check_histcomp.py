# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from HistComp.models import HistCompetitieIndividueel


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
        for obj in (HistCompetitieIndividueel
                    .objects
                    .filter(histcompetitie__seizoen=seizoen,
                            histcompetitie__comp_type=comp_type)
                    .select_related('histcompetitie')
                    .order_by('histcompetitie__boog_str',
                              '-gemiddelde',
                              'rank')):     # bij gelijk gemiddelde

            if obj.histcompetitie.pk != prev_histcomp_pk:
                self.stdout.write('\n[INFO] %s, %s' % (obj.histcompetitie.seizoen, obj.histcompetitie.boog_str))
                prev_histcomp_pk = obj.histcompetitie.pk
                prev_rank = 0

            if prev_rank:
                if obj.rank != prev_rank + 1:
                    self.stdout.write('[WARNING] obj pk=%s met rank=%s niet opvolgend (prev=%s)' % (obj.pk, obj.rank, prev_rank))
            prev_rank = obj.rank

        # for

# end of file
