# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils.formats import localize
from Competitie.models import Regiocompetitie
from Functie.definities import Rollen
from Score.operations import wanneer_ag_vastgesteld
from types import SimpleNamespace


def get_kaartjes_regio(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina gerelateerd aan de Regiocompetitie
        comp.fase_indiv/fase_teams zijn gezet.

        Regiocompetitie loopt vanaf fase A t/m G.
    """

    if rol_nu == Rollen.ROL_BB:

        if not comp.klassengrenzen_vastgesteld:
            # AG vaststellen
            tekst = "AG vaststellen voor alle sporters a.h.v. uitslag vorig seizoen "
            afstand_meter = int(comp.afstand)
            datum = wanneer_ag_vastgesteld(afstand_meter)
            if datum:
                tekst += "(laatst gedaan op %s)" % localize(datum.date())
            else:
                tekst += "(eerste keer)"

            url = reverse('CompBeheer:ag-vaststellen-afstand', kwargs={'afstand': comp.afstand})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="Aanvangsgemiddelden",
                        icoon="how_to_reg",
                        tekst=tekst,
                        url=url)
            kaartjes_algemeen.append(kaartje)

            # klassengrenzen vaststellen
            url = reverse('CompBeheer:klassengrenzen-vaststellen', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="Zet klassengrenzen",
                        icoon="equalizer",
                        tekst="Klassengrenzen vaststellen (eenmalige actie).",
                        url=url)
            kaartjes_algemeen.append(kaartje)

    if rol_nu == Rollen.ROL_BKO:

        # Doorzetten regiocompetitie naar RK
        if comp.fase_indiv == 'G':
            url = reverse('CompBeheer:bko-doorzetten-regio-naar-rk', kwargs={'comp_pk': comp.pk})
            kaartje = SimpleNamespace(
                prio=5,
                titel="Doorzetten",
                icoon="mediation",
                tekst="%s doorzetten naar de volgende fase (regio naar RK)" % comp.beschrijving,
                url=url)
            kaartjes_algemeen.append(kaartje)

    if rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO):

        # laat de regio instellingen zien voor alle relevante regios
        url = reverse('CompLaagRegio:regio-instellingen-globaal', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                        prio=5,
                        titel="Regio keuzes",
                        icoon="flaky",
                        tekst="Overzicht van de keuzes gemaakt per regio",
                        url=url)
        kaartjes_teams.append(kaartje)

        # laat alle teams zien, ook de teams die nog niet af zijn of nog niet in een poule zitten
        # vanaf fase F laten we dit niet meer zien en komen de RK Teams in beeld
        if 'B' <= comp.fase_teams <= 'F':
            url = reverse('CompLaagRegio:regio-teams-alle', kwargs={'comp_pk': comp.pk, 'subset': 'auto'})
            kaartje = SimpleNamespace(
                        prio=5,
                        titel="Regio Teams",
                        icoon="gamepad",
                        tekst="Alle aangemelde teams voor de regio teamcompetitie.",
                        url=url)
            kaartjes_teams.append(kaartje)

    if rol_nu == Rollen.ROL_RCL:

        # pak de regiocompetitie erbij
        try:
            regiocomp = Regiocompetitie.objects.select_related('nhb_regio').get(competitie=comp, functie=functie_nu)
        except Regiocompetitie.DoesNotExist:
            # verkeerde RCL (Indoor / 25m1pijl mix-up)
            pass
        else:
            if regiocomp.is_afgesloten:
                # toon het medailles kaartje
                url = reverse('CompLaagRegio:medailles', kwargs={'regio': functie_nu.nhb_regio.regio_nr})
                kaartje = SimpleNamespace(
                            prio=5,
                            titel="Medailles",
                            icoon="military_tech",
                            tekst="Toon de toegekende medailles voor elke klasse.",
                            url=url)
                kaartjes_teams.append(kaartje)
            else:
                if comp.fase_teams <= 'F':
                    # planning regio wedstrijden
                    url = reverse('CompLaagRegio:regio-planning', kwargs={'deelcomp_pk': regiocomp.pk})
                    kaartje = SimpleNamespace(
                                prio=3,
                                titel="Planning Regio %s" % regiocomp.nhb_regio.regio_nr,
                                icoon="pending_actions",
                                tekst="Planning van de wedstrijden voor deze competitie.",
                                url=url)
                    kaartjes_indiv.append(kaartje)

                    # instellingen regiocompetitie teams
                    url = reverse('CompLaagRegio:regio-instellingen',
                                  kwargs={'comp_pk': comp.pk,
                                          'regio_nr': functie_nu.nhb_regio.regio_nr})
                    kaartje = SimpleNamespace(
                                prio=9,
                                titel="Instelling teams",
                                icoon="flaky",
                                tekst="Instellingen voor de teamcompetitie in de regio.",
                                url=url)
                    kaartjes_teams.append(kaartje)

                if 'F' <= comp.fase_indiv <= 'G':

                    # Scores invoeren
                    url = reverse('CompScores:scores-rcl', kwargs={'deelcomp_pk': regiocomp.pk})
                    kaartje = SimpleNamespace(
                                prio=2,
                                titel="Scores",
                                icoon="edit",
                                tekst="Scores invoeren en aanpassen voor %s voor deze competitie." % regiocomp.nhb_regio.naam,
                                url=url)
                    kaartjes_teams.append(kaartje)

                if comp.fase_teams >= 'C' and regiocomp.regio_organiseert_teamcompetitie:

                    # AG controle
                    url = reverse('CompLaagRegio:regio-ag-controle',
                                  kwargs={'comp_pk': comp.pk,
                                          'regio_nr': functie_nu.nhb_regio.regio_nr})
                    kaartje = SimpleNamespace(
                                prio=7,
                                titel="AG controle",
                                icoon="how_to_reg",
                                tekst="Handmatig ingevoerde aanvangsgemiddelden voor de teamcompetitie.",
                                url=url)
                    kaartjes_teams.append(kaartje)

                    # Regio teams
                    url = reverse('CompLaagRegio:regio-teams', kwargs={'deelcomp_pk': regiocomp.pk})
                    kaartje = SimpleNamespace(
                                    prio=5,
                                    titel="Ingeschreven Teams",
                                    icoon="gamepad",
                                    tekst="Teams voor de regiocompetitie inzien voor deze competitie.",
                                    url=url)
                    kaartjes_teams.append(kaartje)

                    # Poules
                    url = reverse('CompLaagRegio:regio-poules', kwargs={'deelcomp_pk': regiocomp.pk})
                    kaartje = SimpleNamespace(
                                    prio=5,
                                    titel="Team Poules",
                                    icoon="grid_4x4",
                                    tekst="Poules voor directe teamwedstrijden tussen teams in deze regiocompetitie.",
                                    url=url)
                    kaartjes_teams.append(kaartje)

                    if 'F' <= comp.fase_teams <= 'G':

                        # Team ronde
                        url = reverse('CompLaagRegio:start-volgende-team-ronde', kwargs={'deelcomp_pk': regiocomp.pk})
                        kaartje = SimpleNamespace(
                                    prio=1,
                                    titel="Team Ronde",
                                    icoon="mediation",
                                    tekst="Stel de team punten vast en zet de teamcompetitie door naar de volgende ronde.",
                                    url=url)
                        kaartjes_teams.append(kaartje)

                # inschrijvingen
                if comp.is_open_voor_inschrijven():
                    url = reverse('CompInschrijven:lijst-regiocomp-regio',
                                  kwargs={'comp_pk': comp.pk,
                                          'regio_pk': functie_nu.nhb_regio.pk})
                    kaartje = SimpleNamespace(
                                    prio=5,
                                    titel="Inschrijvingen",
                                    icoon="receipt",
                                    tekst="Toon lijst met sporters ingeschreven voor de regiocompetitie.",
                                    url=url)
                    kaartjes_indiv.append(kaartje)

                # Afsluiten regiocompetitie
                if comp.fase_indiv == 'G':
                    url = reverse('CompLaagRegio:afsluiten-regiocomp', kwargs={'deelcomp_pk': regiocomp.pk})
                    kaartje = SimpleNamespace(
                                    prio=5,
                                    titel="Sluit Regiocompetitie",
                                    icoon="done_outline",
                                    tekst="Bevestig eindstand %s voor de %s." % (regiocomp.nhb_regio.naam,
                                                                                 regiocomp.competitie.beschrijving),
                                    url=url)
                    kaartjes_indiv.append(kaartje)

    # end of file
