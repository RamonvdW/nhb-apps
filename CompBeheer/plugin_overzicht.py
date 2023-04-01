# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.definities import DEEL_BK
from Competitie.models import Kampioenschap
from Functie.definities import Rollen
from types import SimpleNamespace


def get_kaartjes_beheer(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina
        comp.fase_indiv/fase_teams zijn gezet
    """

    # Tijdlijn
    url = reverse('Competitie:tijdlijn', kwargs={'comp_pk': comp.pk})
    kaartje = SimpleNamespace(
                    prio=1,
                    titel="Tijdlijn",
                    icoon="schedule",
                    tekst="Toon de fases en planning van deze competitie.",
                    url=url)
    kaartjes_algemeen.append(kaartje)

    # Clusters beheren
    if rol_nu == Rollen.ROL_RCL:
        url = reverse('CompLaagRegio:clusters')
        kaartje = SimpleNamespace(
                    prio=5,
                    titel="Clusters",
                    icoon="group_work",
                    tekst="Verenigingen groeperen in geografische clusters.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    # Toon klassegrenzen (is een openbaar kaartje)
    if comp.klassengrenzen_vastgesteld:
        url = reverse('Competitie:klassengrenzen-tonen', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=5,
                    titel="Wedstrijdklassen",
                    icoon="equalizer",
                    tekst="Toon de wedstrijdklassen, klassengrenzen en blazoenen voor de competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    # Uitslagen / Deelnemers (is een openbaar kaartje)
    if comp.fase_indiv >= 'C':
        url = reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=9,
                    titel="Uitslagenlijsten",
                    icoon="scoreboard",
                    tekst="Toon de deelnemerslijsten en uitslagen van deze competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    if rol_nu == Rollen.ROL_BB:
        # Wijzig datums
        url = reverse('CompBeheer:wijzig-datums', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=3,
                    titel="Wijzig datums",
                    icoon="build",
                    tekst="Belangrijke datums aanpassen voor de fases van deze nieuwe competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

        # TODO: Competitie afsluiten

    # samenvoegen kleine klassen
    if rol_nu == Rollen.ROL_BKO:
        if comp.fase_indiv == 'N':
            url = reverse('CompBeheer:bko-bk-indiv-kleine-klassen', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                            prio=2,
                            titel="Doorzetten",
                            icoon="mediation",
                            tekst="Kleine BK klassen zijn samengevoegd; deelnemerslijst openbaar maken.",
                            url=url)
            kaartjes_indiv.append(kaartje)

        if comp.fase_teams == 'N':
            url = reverse('CompBeheer:bko-bk-teams-kleine-klassen', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                            prio=2,
                            titel="Doorzetten",
                            icoon="mediation",
                            tekst="Kleine BK teams klassen zijn samengevoegd; deelnemerslijst openbaar maken.",
                            url=url)
            kaartjes_teams.append(kaartje)

# end of file
