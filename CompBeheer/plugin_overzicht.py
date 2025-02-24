# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Functie.definities import Rol
from types import SimpleNamespace


def get_kaartjes_beheer(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina
        comp.fase_indiv/fase_teams zijn gezet
    """

    # Tijdlijn
    url = reverse('CompBeheer:tijdlijn', kwargs={'comp_pk': comp.pk})
    kaartje = SimpleNamespace(
                    prio=1,
                    titel="Tijdlijn",
                    icoon="schedule",
                    tekst="Toon de fases en planning van deze competitie.",
                    url=url)
    kaartjes_algemeen.append(kaartje)

    # Verenigingen
    url = reverse('Vereniging:lijst')
    if rol_nu == Rol.ROL_RCL:
        tekst = "Overzicht van de verenigingen in jouw regio"
    elif rol_nu == Rol.ROL_RKO:
        tekst = "Overzicht van de verenigingen, accommodaties en indeling in clusters in jouw rayon."
    else:
        tekst = "Landelijk overzicht van de verenigingen, accommodaties en indeling in clusters."
    kaartje = SimpleNamespace(
                    prio=6,
                    titel="Verenigingen",
                    icoon="share_location",
                    tekst=tekst,
                    url=url)
    kaartjes_algemeen.append(kaartje)

    # Beheerders
    url = reverse('Functie:lijst-beheerders')
    kaartje = SimpleNamespace(
                    prio=7,
                    titel="Beheerders",
                    icoon="face",
                    tekst="Toon wie beheerders van de bondscompetitie zijn, " +
                          "koppel andere beheerders of wijzig contactgegevens.",
                    url=url)
    kaartjes_algemeen.append(kaartje)

    # Clusters beheren
    if rol_nu == Rol.ROL_RCL:
        if comp.afstand == functie_nu.comp_type:
            url = reverse('CompLaagRegio:clusters')
            kaartje = SimpleNamespace(
                        prio=8,
                        titel="Clusters",
                        icoon="group_work",
                        tekst="Verenigingen groeperen in geografische clusters.",
                        url=url)
            kaartjes_algemeen.append(kaartje)

    # Toon klassengrenzen (is een openbaar kaartje)
    if comp.klassengrenzen_vastgesteld:
        url = reverse('Competitie:klassengrenzen-tonen', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})
        kaartje = SimpleNamespace(
                    prio=9,
                    titel="Wedstrijdklassen",
                    icoon="equalizer",
                    tekst="Toon de wedstrijdklassen, klassengrenzen en blazoenen voor de competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    # Uitslagen / Deelnemers (is een openbaar kaartje)
    if comp.fase_indiv >= 'C':
        url = reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})
        kaartje = SimpleNamespace(
                    prio=4,
                    titel="Uitslagenlijsten",
                    icoon="scoreboard",
                    tekst="Toon de deelnemerslijsten en uitslagen van deze competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    if rol_nu == Rol.ROL_BB:
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
    if rol_nu == Rol.ROL_BKO:
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
