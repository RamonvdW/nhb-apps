# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieTeam


class Command(BaseCommand):
    help = "Controleer vereniging voor alle team leden"

    def handle(self, *args, **options):
        for team in RegiocompetitieTeam.objects.select_related('vereniging'):
            for lid in team.leden.select_related('bij_vereniging', 'sporterboog__sporter__bij_vereniging').all():
                if lid.bij_vereniging != team.vereniging:
                    # dit gebeurt nooit
                    self.stdout.write('[WARNING] Team %s van vereniging %s heeft sportboog %s van vereniging %s' % (
                        team, team.vereniging.ver_nr_en_naam(), lid, lid.bij_vereniging))

                if lid.sporterboog.sporter.bij_vereniging != lid.bij_vereniging:
                    self.stdout.write('[WARNING] Team %s van vereniging %s heeft sportboog %s van vereniging %s die overgestapt is naar vereniging %s' % (
                        team, team.vereniging.ver_nr_en_naam(), lid, lid.bij_vereniging, lid.sporterboog.sporter.bij_vereniging))
        # for

# end of file
