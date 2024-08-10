# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.definities import DEEL_RK
from Competitie.models import Kampioenschap
from Functie.definities import Rollen
from types import SimpleNamespace


def get_kaartjes_rayon(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina gerelateerd aan de Rayonkampioenschappen
        comp.fase_indiv/fase_teams zijn gezet.

        De rayonkampioenschappen lopen van fase J tot en met L.
    """

    if rol_nu == Rollen.ROL_BKO:

        # Klassengrenzen vaststellen voor RK/BK teams
        if not comp.klassengrenzen_vastgesteld_rk_bk and comp.fase_teams == 'J':
            url = reverse('CompBeheer:klassengrenzen-vaststellen-rk-bk-teams', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Doorzetten",
                        icoon="mediation",
                        tekst="Open inschrijving RK teams sluiten en " +
                              "de klassengrenzen voor het RK teams en BK teams vaststellen.",
                        url=url)
            kaartjes_teams.append(kaartje)

        # blanco resultaat geven
        if comp.fase_indiv == 'L':
            url = reverse('CompLaagRayon:geef-blanco-resultaat', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=10,
                        titel="Blanco resultaat",
                        icoon="fast_forward",
                        tekst="Sporters die niet hebben kunnen schieten een blanco resultaat geven",
                        url=url)
            kaartjes_indiv.append(kaartje)

        # afsluiten RK individueel / doorzetten naar BK individueel
        if comp.fase_indiv == 'L':
            url = reverse('CompBeheer:bko-rk-indiv-doorzetten-naar-bk', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Doorzetten",
                        icoon="mediation",
                        tekst="%s individueel doorzetten naar de volgende fase (RK naar BK)" % comp.beschrijving,
                        url=url)
            kaartjes_indiv.append(kaartje)

        # afsluiten RK teams / doorzetten naar BK teams
        if comp.fase_teams == 'L':
            url = reverse('CompBeheer:bko-rk-teams-doorzetten-naar-bk', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Doorzetten",
                        icoon="mediation",
                        tekst="%s teams doorzetten naar de volgende fase (RK naar BK)" % comp.beschrijving,
                        url=url)
            kaartjes_teams.append(kaartje)

        # inschreven RK teams (open inschrijving RK teams tijdens fase F)
        if 'F' <= comp.fase_teams <= 'L':
            url = reverse('CompLaagRayon:rayon-teams-alle', kwargs={'comp_pk': comp.pk, 'subset': 'auto'})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="RK teams",
                        icoon="api",
                        tekst="Alle aangemelde teams voor de Rayonkampioenschappen.",
                        url=url)
            kaartjes_teams.append(kaartje)

        # extra RK deelnemer
        if 'J' <= comp.fase_indiv <= 'K':
            url = reverse('CompLaagRayon:rayon-extra-deelnemer', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="Extra deelnemer",
                        icoon="person_add",
                        tekst="Voeg een regiocompetitie deelnemer toe aan het RK (aspirant of na score correctie).",
                        url=url)
            kaartjes_indiv.append(kaartje)

    elif rol_nu == Rollen.ROL_RKO:

        # zoek het RK kampioenschap erbij
        try:
            deelkamp_rk = (Kampioenschap
                           .objects
                           .select_related('competitie',
                                           'rayon')
                           .get(deel=DEEL_RK,
                                competitie=comp,
                                functie=functie_nu,
                                is_afgesloten=False))
        except Kampioenschap.DoesNotExist:
            # verkeerde RKO (Indoor / 25m1pijl mix-up)
            pass
        else:
            # Planning RK wedstrijden
            if not deelkamp_rk.is_afgesloten:
                url = reverse('CompLaagRayon:planning', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                kaartje = SimpleNamespace(
                            prio=3,
                            titel="Planning %s" % deelkamp_rk.rayon.naam,
                            icoon="pending_actions",
                            tekst="Planning voor %s voor deze competitie." % deelkamp_rk.rayon.naam,
                            url=url)
                kaartjes_algemeen.append(kaartje)

            # RK selectie individueel
            if 'J' <= comp.fase_indiv <= 'L':
                url = reverse('CompLaagRayon:lijst-rk', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                kaartje = SimpleNamespace(
                            prio=5,
                            titel="RK selectie",
                            icoon="rule",
                            tekst="Selectie van sporters voor de Rayonkampioenschappen.",
                            url=url)
                kaartjes_indiv.append(kaartje)

            # RK limieten (indiv & teams)
            if 'J' <= comp.fase_indiv <= 'L' or 'J' <= comp.fase_teams <= 'L':
                url = reverse('CompLaagRayon:limieten', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                kaartje = SimpleNamespace(
                            prio=5,
                            titel="RK limieten",
                            icoon="accessibility_new",
                            tekst="Maximum aantal deelnemers in elke wedstrijdklasse van jouw RK instellen.",
                            url=url)
                kaartjes_indiv.append(kaartje)
                kaartjes_teams.append(kaartje)

            # Ingeschreven RK teams (inschrijving opent tijdens fase F)
            if 'F' <= comp.fase_teams <= 'L':
                url = reverse('CompLaagRayon:rayon-teams', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                kaartje = SimpleNamespace(
                            prio=4,
                            titel="RK teams",
                            icoon="api",
                            tekst="Aangemelde teams voor de Rayonkampioenschappen in %s." % deelkamp_rk.rayon.naam,
                            url=url)
                kaartjes_teams.append(kaartje)


# end of file
