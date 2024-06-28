# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie
from Competitie.operations import (uitslag_regio_indiv_naar_histcomp, uitslag_regio_teams_naar_histcomp,
                                   uitslag_rk_indiv_naar_histcomp, uitslag_rk_teams_naar_histcomp,
                                   uitslag_bk_indiv_naar_histcomp, uitslag_bk_teams_naar_histcomp)


# TODO: is dit commando nog nodig?

class Command(BaseCommand):
    help = "Zet competitie uitslag om in historische uitslag"

    def add_arguments(self, parser):
        parser.add_argument('comptype', nargs=1, choices=('18', '25'),
                            help="competitie type: 18 of 25")

    def handle(self, *args, **options):
        # self.stderr.write("import individuele competitie historie. args=%s, options=%s" % (repr(args), repr(options)))
        comp_type = options['comptype'][0]

        comps = Competitie.objects.filter(afstand=comp_type).order_by('begin_jaar')
        if len(comps) == 0:
            self.stderr.write('[ERROR] Geen actieve competitie gevonden')
            return

        comp = comps[0]     # neem de oudste
        self.stdout.write('[INFO] Competitie: %s' % comp)

        self.stdout.write('[INFO] Regio indiv')
        uitslag_regio_indiv_naar_histcomp(comp)

        self.stdout.write('[INFO] Regio teams')
        uitslag_regio_teams_naar_histcomp(comp)

        self.stdout.write('[INFO] RK indiv')
        uitslag_rk_indiv_naar_histcomp(comp)

        self.stdout.write('[INFO] RK teams')
        uitslag_rk_teams_naar_histcomp(comp)

        self.stdout.write('[INFO] BK indiv')
        uitslag_bk_indiv_naar_histcomp(comp)

        self.stdout.write('[INFO] BK teams')
        uitslag_bk_teams_naar_histcomp(comp)

        self.stdout.write('[INFO] Done')

# end of file
