# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies """

from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Geo.models import Rayon


def iter_indiv_wedstrijdformulieren(comp: Competitie):
    """ generator voor alle individuele wedstrijdformulieren

        generates tuples:
            (afstand, is_bk, klasse_pk, rayon_nr, fname)
    """
    afstand = int(comp.afstand)
    rayon_nrs = list(Rayon.objects.all().values_list('rayon_nr', flat=True))

    for klasse in CompetitieIndivKlasse.objects.filter(competitie=comp, is_ook_voor_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_individueel-rayon%s_" % rayon_nr
            fname += klasse_str
            #              is_bk
            yield afstand, False, klasse.pk, rayon_nr, fname
        # for

        # BK programma's
        fname = "bk-programma_individueel_" + klasse_str
        #              is_bk
        yield afstand, True, klasse.pk, 0, fname
    # for


def iter_teams_wedstrijdformulieren(comp: Competitie):
    """ generator voor alle teams wedstrijdformulieren

        generates tuples:
            (afstand, is_bk, klasse_pk, rayon_nr, fname)
    """
    # uitgezet omdat we het Excel formulier nog gebruiken
    return

    afstand = int(comp.afstand)
    rayon_nrs = list(Rayon.objects.all().values_list('rayon_nr', flat=True))

    for klasse in CompetitieTeamKlasse.objects.filter(competitie=comp, is_voor_teams_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        is_bk = False
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_teams-rayon%s_" % rayon_nr
            fname += klasse_str
            yield afstand, is_bk, klasse.pk, rayon_nr, fname
        # for

        # BK programma's
        is_bk = True
        rayon_nr = 0
        fname = "bk-programma_teams_" + klasse_str
        yield afstand, is_bk, klasse.pk, rayon_nr, fname
    # for


# end of file
