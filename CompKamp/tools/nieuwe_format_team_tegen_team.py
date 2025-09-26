import itertools
from typing import Tuple
import sys


# TODO: met 7 teams wordt er een ronde toegevoegd, dat zou niet hoeven want met 8 (en 1 BYE) kan ook in 7 rondes

class MakeSchedule:

    def __init__(self, teams):
        self.nr_of_teams = len(teams)
        self._teams = teams
        self._avail = list(itertools.combinations(teams, 2))
        self._counts = dict()       # number of matches per team, to minimize waiting
        for t in self._teams:
            self._counts[t] = 0
        # for
        self._variaties = dict()

    def _set_variaties(self, variables):
        self._variaties = dict()
        for ronde_nr in range(10):
            self._variaties[ronde_nr] = 0
        # for
        ronde_nr = 0
        for v in variables:
            ronde_nr += 1
            self._variaties[ronde_nr] = int(v)
        # for

    def _get_order(self, variable) -> Tuple[list, list]:
        # return the order in which to schedule the teams
        # this attempt to avoid teams from having to wait multiple rounds
        order = [(c, t)
                 for t, c in self._counts.items()]
        order.sort()        # lowest count first
        # print(order)
        teams = [t
                 for c, t in order]

        order = [(self._counts[t1] + self._counts[t2], t1, t2)
                 for t1, t2 in self._avail]
        order.sort()        # lowest first

        if variable > 0:
            tup = order.pop(variable)
            order.insert(0, tup)
        # print(order)

        avail = [(t1, t2)
                 for c, t1, t2 in order]

        return teams, avail

    def _next_matches(self, ronde_nr):
        # pick matches to keep all teams busy
        v = self._variaties[ronde_nr]
        teams, avail = self._get_order(v)
        matches = list()
        t_done = list()
        for t in teams:
            if t not in t_done:
                # find a match for this team
                for team_tup in avail:
                    if t in team_tup:
                        t1, t2 = team_tup
                        if t1 not in t_done and t2 not in t_done:
                            self._avail.remove(team_tup)
                            avail.remove(team_tup)
                            if t2 != 'z':       # skip bye match
                                matches.append(team_tup)
                                t_done.extend(list(team_tup))
                                self._counts[t1] += 1
                                self._counts[t2] += 1
                            break
                # for
        # for
        free_teams = [t
                      for t in self._teams
                      if t not in t_done
                      if t != 'z']
        matches.sort()
        return matches, free_teams

    def _maak_schema(self, variaties):
        self._set_variaties(variaties)
        schema = list()
        ronde_nr = 0
        while ronde_nr < 99:
            ronde_nr += 1
            matches, free_teams = self._next_matches(ronde_nr)
            if len(matches):
                tup = ('Ronde %s' % ronde_nr, matches, free_teams)
                schema.append(tup)
            else:
                ronde_nr = 99
        # for
        return schema

    def run(self, variaties):
        schema = self._maak_schema(variaties)
        for ronde_str, matches, free_teams in schema:
            print('')
            print(ronde_str)
            print('-------------')
            for t1, t2 in matches:
                print("%s-%s" % (t1, t2))
            # for
            if free_teams:
                print('Free teams: %s' % ", ".join(free_teams))
        # for


if len(sys.argv) < 2:
    print("Hoeveel teams? (1..8)")
else:
    aantal = int(sys.argv[1])
    print('rest:', aantal % 2)
    team_letters = "ABCDEFGH"[:aantal]
    if aantal == 97:
        # maak even aantal teams door een Bye toe te voegen
        team_letters += 'z'

    var_lst = [int(arg)
               for arg in sys.argv[2:]]
    MakeSchedule(team_letters).run(var_lst)

# end of file
