# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import DeelCompetitie, LAAG_REGIO, RegioCompetitieSchutterBoog


class Command(BaseCommand):
    help = "Zoek teamschutters zonder AG"

    def __init__(self):
        super().__init__()

        self.deelcomp_poule_msg = ''
        self.teams = list()

    def handle(self, *args, **options):

        for afstand in ('18', '25'):
            deelcomp_pks = (DeelCompetitie
                            .objects
                            .filter(competitie__afstand=afstand,
                                    laag=LAAG_REGIO,
                                    regio_organiseert_teamcompetitie=True)
                            .order_by('nhb_regio__regio_nr')
                            .values_list('pk', flat=True))

            for deelnemer in (RegioCompetitieSchutterBoog
                              .objects
                              .filter(deelcompetitie__pk__in=deelcomp_pks,
                                      inschrijf_voorkeur_team=True,
                                      ag_voor_team_mag_aangepast_worden=True,
                                      ag_voor_team__lte="0.1")
                              .select_related('bij_vereniging',
                                              'bij_vereniging__regio',
                                              'sporterboog__sporter')
                              .order_by('bij_vereniging__regio__regio_nr',
                                        'bij_vereniging__ver_nr',
                                        'sporterboog__sporter__lid_nr')):
                print('%2s  %3s  %-30s  %s' % (afstand,
                                               deelnemer.bij_vereniging.regio.regio_nr,
                                               str(deelnemer.bij_vereniging)[:30],
                                               deelnemer))
            # for
        # for

# end of file
