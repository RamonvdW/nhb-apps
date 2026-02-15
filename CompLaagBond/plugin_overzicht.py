# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.definities import DEEL_BK
from Competitie.models import Kampioenschap
from Functie.definities import Rol
from types import SimpleNamespace


def get_kaartjes_bond(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina voor de Bondskampioenschappen
        comp.fase_indiv/fase_teams zijn gezet

        De bondskampioenschappen lopen van fase N tot en met P
    """

    if rol_nu == Rol.ROL_BKO:

        # BK erbij pakken
        deelkamp_bk = Kampioenschap.objects.select_related('competitie').get(competitie=comp, deel=DEEL_BK)

        # Planning BK wedstrijden
        if not deelkamp_bk.is_afgesloten:
            url = reverse('CompLaagBond:planning', kwargs={'deelkamp_pk': deelkamp_bk.pk})
            kaartje = SimpleNamespace(
                        prio=3,
                        titel="Planning",
                        sv_icon="comp planning",
                        tekst="Landelijke planning voor deze competitie.",
                        url=url)
            kaartjes_algemeen.append(kaartje)

        # BK kleine klassen samenvoegen
        if comp.fase_indiv == 'N':
            url = reverse('CompLaagBond:kleine-klassen-samenvoegen-indiv', kwargs={'deelkamp_pk': deelkamp_bk.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Kleine klassen",
                        sv_icon="comp kleine klassen",
                        tekst="Kleine wedstrijdklassen samenvoegen voor de individuele Bondskampioenschappen.",
                        url=url)
            kaartjes_indiv.append(kaartje)

        # TODO: implementeer deze optie. Voorbeeld: maar 1 TR team in BK finale -> samenvoegen met BB
        # if comp.fase_teams == 'N':
        #     url = reverse('CompLaagBond:kleine-klassen-samenvoegen-teams', kwargs={'deelkamp_pk': deelkamp_bk.pk})
        #     kaartje = SimpleNamespace(
        #                 prio=5,
        #                 titel="Kleine klassen",
        #                 icoon="merge",
        #                 tekst="Kleine wedstrijdklassen samenvoegen voor de Bondskampioenschappen teams.",
        #                 url=url)
        #     kaartjes_teams.append(kaartje)

        # BK selectie (individueel)
        if 'N' <= comp.fase_indiv <= 'P':
            url = reverse('CompLaagBond:bk-selectie', kwargs={'deelkamp_pk': deelkamp_bk.pk})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="BK selectie",
                        sv_icon="comp bk selectie",
                        tekst="Selectie van sporters voor de Bondskampioenschappen.",
                        url=url)
            kaartjes_indiv.append(kaartje)

        # BK teams aanmelden/afmelden
        if 'N' <= comp.fase_teams <= 'P':
            url = reverse('CompLaagBond:bk-teams', kwargs={'deelkamp_pk': deelkamp_bk.pk})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="BK teams",
                        sv_icon="comp bk teams",
                        tekst="Aanmelden / afmelden teams voor de BK.",
                        url=url)
            kaartjes_teams.append(kaartje)

        # BK limieten (individueel en teams)
        if 'L' <= comp.fase_indiv <= 'P' or 'L' <= comp.fase_teams <= 'P':
            url = reverse('CompLaagBond:wijzig-limieten', kwargs={'deelkamp_pk': deelkamp_bk.pk})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="BK limieten",
                        sv_icon="comp limieten",
                        tekst="Maximum aantal deelnemers in elke wedstrijdklasse van jouw BK instellen.",
                        url=url)
            if 'L' <= comp.fase_indiv <= 'P':
                kaartjes_indiv.append(kaartje)
            if 'L' <= comp.fase_teams <= 'P':
                kaartjes_teams.append(kaartje)

        # Doorzetten BK individueel / bevestig uitslag
        if comp.fase_indiv == 'P':
            url = reverse('CompBeheer:bko-bevestig-eindstand-bk-indiv', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Doorzetten",
                        sv_icon="comp doorzetten",
                        tekst="%s uitslag BK individueel bevestigen" % comp.beschrijving,
                        url=url)
            kaartjes_indiv.append(kaartje)

        # Doorzetten BK teams / bevestig uitslag
        if comp.fase_teams == 'P':
            url = reverse('CompBeheer:bko-bevestig-eindstand-bk-teams', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=2,
                        titel="Doorzetten",
                        sv_icon="comp doorzetten",
                        tekst="%s uitslag BK teams bevestigen" % comp.beschrijving,
                        url=url)
            kaartjes_teams.append(kaartje)


# end of file
