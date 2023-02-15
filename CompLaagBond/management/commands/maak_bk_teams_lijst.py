# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Competitie.models import (Competitie, CompetitieTeamKlasse, DEEL_RK, DEEL_BK,
                               Kampioenschap, KampioenschapTeam, KampioenschapSporterBoog)


class Command(BaseCommand):
    help = "Maak BK teams deelnemerslijst"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dryrun = False

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=int, help='Competitie afstand (18/25)')
        parser.add_argument('--dryrun', action='store_true', help='Uitproberen')

    def _maak_bk_teams(self, comp):

        if comp.afstand == '18':
            aantal_pijlen = 2.0 * 30
        else:
            aantal_pijlen = 2.0 * 25

        # zoek het BK erbij
        deelkamp_bk = Kampioenschap.objects.select_related('competitie').get(deel=DEEL_BK, competitie=comp)

        # verwijder de al aangemaakte teams
        qset = KampioenschapTeam.objects.filter(kampioenschap=deelkamp_bk).all()
        aantal = qset.count()
        if aantal > 0:
            self.stdout.write('[INFO] Alle %s bestaande BK teams worden verwijderd' % aantal)
            qset.delete()

        bulk = list()

        for klasse in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .order_by('volgorde')):

            self.stdout.write('[INFO] Team klasse: %s' % klasse)

            # haal alle teams uit de RK op
            for rk_team in (KampioenschapTeam
                            .objects
                            .filter(kampioenschap__deel=DEEL_RK,
                                    kampioenschap__competitie=comp,
                                    team_klasse=klasse,
                                    result_rank__gte=1)
                            .select_related('vereniging',
                                            'team_type')
                            .prefetch_related('gekoppelde_leden')):

                ag = rk_team.result_teamscore / aantal_pijlen

                team = KampioenschapTeam(
                            kampioenschap=deelkamp_bk,
                            vereniging=rk_team.vereniging,
                            volg_nr=rk_team.volg_nr,
                            team_type=rk_team.team_type,
                            team_naam=rk_team.team_naam,
                            team_klasse=klasse,
                            aanvangsgemiddelde=ag)
                team.save()
                self.stdout.write('[INFO] Maak team %s.%s (%s)' % (
                                    rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_naam))

                # koppel de RK deelnemers aan het BK team
                pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)
                team.gekoppelde_leden.set(pks)
            # for
        # for

    def handle(self, *args, **options):
        afstand = options['afstand']
        self.dryrun = options['dryrun']

        qset = Competitie.objects.filter(is_afgesloten=False, afstand=afstand).order_by('begin_jaar')
        if qset.count() == 0:
            self.stderr.write('[ERROR] Geen competitie beschikbaar')
            return

        comp = qset[0]
        self.stdout.write('[INFO] Geselecteerde competitie: %s' % comp)

        self._maak_bk_teams(comp)


# end of file
