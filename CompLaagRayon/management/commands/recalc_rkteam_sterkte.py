# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# bereken de team sterktes opnieuw
# door een foutje was deze berekend over de 3 laagste gemiddelden in plaats van de 3 hoogste

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, KampioenschapTeam


class Command(BaseCommand):
    help = "Bereken team sterkte voor alle RK teams opnieuw"

    def handle(self, *args, **options):

        for comp in Competitie.objects.filter(is_afgesloten=False):
            comp.bepaal_fase()
            self.stdout.write('[INFO] Competitie %s is in fase_teams=%s' % (comp, comp.fase_teams))

            if comp.fase_teams == 'J':
                count = 0
                for rk_team in (KampioenschapTeam
                                .objects
                                .filter(kampioenschap__competitie=comp)
                                .prefetch_related('gekoppelde_leden')):

                    ags = list(rk_team.gekoppelde_leden.values_list('gemiddelde', flat=True))
                    if len(ags) >= 3:
                        ags.sort(reverse=True)  # hoogste eerst
                        ag = sum(ags[:3])
                    else:
                        ag = 0.0

                    if ag != rk_team.aanvangsgemiddelde:
                        self.stdout.write('Team %s: %.3f --> %.3f' % (rk_team, rk_team.aanvangsgemiddelde, ag))
                        count += 1
                        rk_team.aanvangsgemiddelde = ag
                        rk_team.save(update_fields=['aanvangsgemiddelde'])
                # for

                self.stdout.write('[INFO] Aantal wijzigingen: %s' % count)
        # for


# end of file
