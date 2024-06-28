# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieRondeTeam


class Command(BaseCommand):
    help = "Zoek dubbele ronde teams"

    def handle(self, *args, **options):

        self.stdout.write('Ronde teams die dubbel in de database staan:')

        found = dict()      # [(comp_pk, ronde_nr, team_pk)] = ronde team

        count = dict()      # [(comp_pk, regio_nr)] = [ronde_nr] = aantal

        for ronde_team in (RegiocompetitieRondeTeam
                           .objects
                           .select_related('team__regiocompetitie__competitie',
                                           'team__regiocompetitie__regio',
                                           'team__team_type',
                                           'team__vereniging')
                           .order_by('team__regiocompetitie__competitie',
                                     'ronde_nr',
                                     'team__pk')):

            tup = (ronde_team.team.regiocompetitie.competitie.pk,
                   ronde_team.ronde_nr,
                   ronde_team.team.vereniging.ver_nr,
                   ronde_team.team.team_type.pk,
                   ronde_team.team.team_naam)

            try:
                other_team = found[tup]
            except KeyError:
                found[tup] = ronde_team
            else:
                # dubbele!
                self.stdout.write('Dupe team in %s' % ronde_team.team.regiocompetitie)
                self.stdout.write('   %s' % other_team)
                for line in other_team.logboek.split('\n'):
                    self.stdout.write('       %s' % line)
                self.stdout.write('   %s' % ronde_team)
                for line in ronde_team.logboek.split('\n'):
                    self.stdout.write('       %s' % line)

            del tup

            tup2 = (ronde_team.team.regiocompetitie.competitie.pk,
                    ronde_team.team.regiocompetitie.regio.regio_nr)

            try:
                count[tup2][ronde_team.ronde_nr] += 1
            except KeyError:
                try:
                    count[tup2][ronde_team.ronde_nr] = 1
                except KeyError:
                    count[tup2] = dict()
                    count[tup2][ronde_team.ronde_nr] = 1

            del tup2
        # for

        # check dat elk team evenveel rondes heeft (in elke regio en competitie)
        self.stdout.write('Inconsistentie aantal teams per ronde:')
        for tup, counts in count.items():       # per competitie en regio
            comp_pk, regio_nr = tup

            aantal = counts[1]      # baseline
            bad = False
            for check in counts.values():
                if check != aantal:
                    # dit team heeft een afwijkend aantal ronde records
                    bad = True
                    break
            # for

            if bad:
                self.stdout.write('Comp %s regio %s ronde counts: %s' % (comp_pk, regio_nr, repr(counts)))


# end of file
