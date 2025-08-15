# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies """

from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Geo.models import Rayon


def iter_wedstrijdformulieren(comp: Competitie):
    """ generator voor alle wedstrijdformulieren

        generates tuples:
            (afstand, is_teams, is_bk, klasse_pk, fname)
    """
    afstand = int(comp.afstand)
    rayon_nrs = list(Rayon.objects.all().values_list('rayon_nr', flat=True))

    for klasse in CompetitieIndivKlasse.objects.filter(competitie=comp, is_ook_voor_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_individueel-rayon%s_" % rayon_nr
            fname += klasse_str
            #            is_team  is_bk
            yield afstand, False, False, klasse.pk, fname
        # for

        # BK programma
        fname = "bk-programma_individueel_" + klasse_str
        #            is_team  is_bk
        yield afstand, False, True, klasse.pk, fname
    # for

    for klasse in CompetitieTeamKlasse.objects.filter(competitie=comp, is_voor_teams_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_teams-rayon%s_" % rayon_nr
            fname += klasse_str
            #           is_team  is_bk
            yield afstand, True, False, klasse.pk, fname
        # for

        # BK programma
        fname = "bk-programma_teams_" + klasse_str
        #           is_team  is_bk
        yield afstand, True, True, klasse.pk, fname
    # for


# end of file
