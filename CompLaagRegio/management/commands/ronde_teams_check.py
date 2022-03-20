# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import RegiocompetitieRondeTeam


class Command(BaseCommand):
    help = "Zoek dubbele ronde teams"

    @staticmethod
    def afkappen(msg, limiet):
        lengte = len(msg)
        if lengte > limiet:
            msg = msg[:limiet-2]
            if msg[-1] == ' ':
                msg = msg[:-1]
            msg += '..'
        return msg

    def handle(self, *args, **options):

        self.stdout.write('Ronde teams die dubbel in de database staan:')

        found = dict()      # [(comp_pk, ronde_nr, team_pk)] = ronde team

        count = dict()      # [(comp_pk, regio_nr)] = [ronde_nr] = aantal

        for ronde_team in (RegiocompetitieRondeTeam
                           .objects
                           .select_related('team__deelcompetitie__competitie',
                                           'team__deelcompetitie__nhb_regio',
                                           'team__team_type',
                                           'team__vereniging')
                           .order_by('team__deelcompetitie__competitie',
                                     'ronde_nr',
                                     'team__pk')):

            tup = (ronde_team.team.deelcompetitie.competitie.pk,
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
                self.stdout.write('Dupe team in %s' % ronde_team.team.deelcompetitie)
                self.stdout.write('   %s' % other_team)
                for line in other_team.logboek.split('\n'):
                    self.stdout.write('       %s' % line)
                self.stdout.write('   %s' % ronde_team)
                for line in ronde_team.logboek.split('\n'):
                    self.stdout.write('       %s' % line)

            del tup

            tup2 = (ronde_team.team.deelcompetitie.competitie.pk,
                    ronde_team.team.deelcompetitie.nhb_regio.regio_nr)

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

        # toon het aantal teams per ronde
        self.stdout.write('Inconsistentie aantal teams per ronde:')
        for tup, counts in count.items():
            comp_pk, regio_nr = tup

            aantal = counts[1]
            bad = False
            for check in counts.values():
                if check != aantal:
                    bad = True
                    break
            # for

            if bad:
                self.stdout.write('Comp %s regio %s ronde counts: %s' % (comp_pk, regio_nr, repr(counts)))


# end of file
