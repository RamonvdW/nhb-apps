# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.templatetags.static import static
from Competitie.definities import DEEL_RK, INSCHRIJF_METHODE_1
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieRonde, Kampioenschap
from Competitie.tijdlijn import maak_comp_fase_beschrijvingen, is_open_voor_inschrijven_rk_teams
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Taken.operations import eval_open_taken
from Wedstrijden.definities import BAAN_TYPE_EXTERN
from types import SimpleNamespace


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nhb_ver'] = ver = self.functie_nu.nhb_ver
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['clusters'] = ver.clusters.all()

        context['toon_wedstrijden'] = self.rol_nu != Rollen.ROL_SEC

        if self.functie_nu.nhb_ver.wedstrijdlocatie_set.exclude(baan_type=BAAN_TYPE_EXTERN).filter(zichtbaar=True).count() > 0:
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details',
                                                          kwargs={'vereniging_pk': ver.pk})

        context['url_externe_locaties'] = reverse('Vereniging:externe-locaties',
                                                  kwargs={'vereniging_pk': ver.pk})

        comps = list()
        deelcomps = list()
        deelkamps_rk = list()

        if self.rol_nu == Rollen.ROL_SEC:
            # SEC
            pass
        else:
            # HWL of WL
            if self.rol_nu == Rollen.ROL_HWL:
                context['toon_wedstrijdkalender'] = True

            if not ver.regio.is_administratief:
                context['toon_competities'] = True

                comps = (Competitie
                         .objects
                         .filter(is_afgesloten=False)
                         .order_by('afstand',
                                   'begin_jaar'))

                deelcomps = (Regiocompetitie
                             .objects
                             .filter(competitie__is_afgesloten=False,
                                     nhb_regio=ver.regio)
                             .select_related('competitie'))

                deelkamps_rk = (Kampioenschap
                                .objects
                                .filter(deel=DEEL_RK,
                                        competitie__is_afgesloten=False,
                                        nhb_rayon=ver.regio.rayon)
                                .select_related('competitie'))

                if (RegiocompetitieRonde
                    .objects
                    .filter(regiocompetitie__is_afgesloten=False,
                            matches__vereniging=ver)).count() > 0:
                    # er zijn wedstrijden voor deze vereniging
                    context['heeft_wedstrijden'] = True

        # bepaal de volgorde waarin de kaartjes getoond worden
        # 0 - tijdlijn
        # 1 - aanmelden
        # 2 - teams regio aanmelden / aanpassen
        # 3 - teams rk
        # 4 - ingeschreven
        # 5 - wie schiet waar (voor inschrijfmethode 1)
        # 6 - uitslagen
        context['kaartjes'] = kaartjes = list()
        prev_jaar = 0
        prev_afstand = 0
        for comp in comps:
            begin_jaar = comp.begin_jaar
            comp.bepaal_fase()

            if prev_jaar != begin_jaar or prev_afstand != comp.afstand:     # pragma: no branch
                if len(kaartjes) and hasattr(kaartjes[-1], 'heading'):
                    # er waren geen kaartjes voor die competitie - meld dat
                    kaartje = SimpleNamespace()
                    kaartje.geen_kaartjes = True
                    kaartjes.append(kaartje)

                if prev_jaar != 0:
                    kaartje = SimpleNamespace()
                    kaartje.einde_blok = True
                    kaartjes.append(kaartje)

                # nieuwe heading aanmaken
                kaartje = SimpleNamespace()
                kaartje.heading = comp.beschrijving
                kaartje.anker = 'competitie_%s' % comp.pk
                kaartje.comp_fase_indiv, kaartje.comp_fase_teams = maak_comp_fase_beschrijvingen(comp)
                kaartjes.append(kaartje)

                prev_jaar = begin_jaar
                prev_afstand = comp.afstand

            # 0 - tijdlijn
            kaartje = SimpleNamespace()
            kaartje.titel = "Tijdlijn"
            kaartje.tekst = 'Toon de fases en planning van de %s.' % comp.beschrijving
            kaartje.icon = 'schedule'
            kaartje.url = reverse('Competitie:tijdlijn', kwargs={'comp_pk': comp.pk})
            kaartjes.append(kaartje)

            # 1 - leden aanmelden voor de competitie (niet voor de WL)
            if comp.fase_indiv < 'F' and self.rol_nu != Rollen.ROL_WL:
                kaartje = SimpleNamespace()
                kaartje.titel = "Aanmelden"
                kaartje.tekst = 'Leden aanmelden voor de %s.' % comp.beschrijving
                kaartje.url = reverse('CompInschrijven:leden-aanmelden', kwargs={'comp_pk': comp.pk})
                if comp.afstand == '18':
                    kaartje.img = static('plein/badge_nhb_indoor.png')
                else:
                    kaartje.img = static('plein/badge_nhb_25m1p.png')
                if comp.fase_indiv < 'C':
                    kaartje.beschikbaar_vanaf = localize(comp.begin_fase_C)
                kaartjes.append(kaartje)

            for deelcomp in deelcomps:
                if deelcomp.competitie == comp:
                    if deelcomp.regio_organiseert_teamcompetitie and comp.fase_teams == 'F' and 1 <= deelcomp.huidige_team_ronde <= 7:
                        # team invallers opgeven
                        kaartje = SimpleNamespace(
                                    titel="Team Invallers",
                                    tekst="Invallers opgeven voor ronde %s van de regiocompetitie." % deelcomp.huidige_team_ronde,
                                    url=reverse('CompLaagRegio:teams-regio-invallers', kwargs={'deelcomp_pk': deelcomp.pk}),
                                    icon='how_to_reg')
                        kaartjes.append(kaartje)
                    else:
                        # 2 - teams aanmaken
                        if deelcomp.regio_organiseert_teamcompetitie and comp.fase_teams == 'C':
                            kaartje = SimpleNamespace()
                            kaartje.titel = "Teams Regio"
                            kaartje.tekst = 'Verenigingsteams voor de regiocompetitie samenstellen.'
                            kaartje.url = reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
                            kaartje.icon = 'gamepad'
                            if comp.fase_indiv < 'C':
                                kaartje.beschikbaar_vanaf = localize(comp.begin_fase_C)
                            kaartjes.append(kaartje)
            # for
            del deelcomp

            # 3 - teams RK
            for deelkamp_rk in deelkamps_rk:
                if deelkamp_rk.competitie == comp:
                    if deelkamp_rk.heeft_deelnemerslijst:
                        if self.rol_nu != Rollen.ROL_WL:
                            if 'J' <= comp.fase_indiv <= 'K':
                                # RK voorbereidende fase
                                kaartje = SimpleNamespace()
                                kaartje.titel = "Deelnemers RK"
                                kaartje.tekst = "Sporters van de vereniging aan-/afmelden voor het RK"
                                kaartje.url = reverse('CompLaagRayon:lijst-rk-ver',
                                                      kwargs={'deelkamp_pk': deelkamp_rk.pk})
                                kaartje.icon = 'rule'
                                kaartjes.append(kaartje)

                    if self.rol_nu != Rollen.ROL_WL:
                        is_open, vanaf_datum = is_open_voor_inschrijven_rk_teams(comp)
                        if is_open or vanaf_datum:
                            kaartje = SimpleNamespace()
                            kaartje.titel = "Teams RK"
                            kaartje.tekst = "Verenigingsteams voor de rayonkampioenschappen samenstellen."
                            kaartje.url = reverse('CompLaagRayon:teams-rk', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                            kaartje.icon = 'api'
                            # niet beschikbaar maken tot een paar weken na de eerste regiowedstrijd
                            if vanaf_datum:
                                kaartje.beschikbaar_vanaf = localize(vanaf_datum)
                            kaartjes.append(kaartje)
                        else:
                            if 'J' <= comp.fase_indiv <= 'K':
                                # RK voorbereidende fase
                                kaartje = SimpleNamespace()
                                kaartje.titel = "Teams RK"
                                kaartje.tekst = "Verenigingsteams voor de rayonkampioenschappen inzien."
                                kaartje.url = reverse('CompLaagRayon:teams-rk', kwargs={'deelkamp_pk': deelkamp_rk.pk})
                                kaartje.icon = 'api'
                                kaartjes.append(kaartje)


            # for
            del deelkamp_rk

            for deelcomp in deelcomps:
                if deelcomp.competitie == comp:
                    # 4 - ingeschreven
                    if 'C' <= comp.fase_indiv <= 'G':         # vanaf RK fase niet meer tonen
                        kaartje = SimpleNamespace()
                        kaartje.titel = "Ingeschreven"
                        kaartje.tekst = "Overzicht ingeschreven leden."
                        kaartje.url = reverse('CompInschrijven:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})
                        if comp.afstand == '18':
                            kaartje.img = static('plein/badge_nhb_indoor.png')
                        else:
                            kaartje.img = static('plein/badge_nhb_25m1p.png')
                        kaartjes.append(kaartje)

                    # 5 - wie schiet waar
                    if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1 and 'C' <= comp.fase_indiv <= 'F':
                        kaartje = SimpleNamespace()
                        kaartje.titel = "Wie schiet waar?"
                        kaartje.tekst = 'Overzicht gekozen wedstrijden.'
                        kaartje.url = reverse('CompLaagRegio:wie-schiet-waar', kwargs={'deelcomp_pk': deelcomp.pk})
                        kaartje.icon = 'gamepad'
                        # if comp.fase_indiv < 'C':
                        #     kaartje.beschikbaar_vanaf = localize(comp.begin_fase_C)
                        kaartjes.append(kaartje)
            # for

            if comp.fase_indiv >= 'C':
                # 5 - uitslagen
                kaartje = SimpleNamespace(
                                titel="Uitslagenlijsten",
                                tekst="Toon de deelnemerslijsten en uitslagen van deze competitie.",
                                icon='scoreboard',
                                url=reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}))
                kaartjes.append(kaartje)
        # for

        if len(kaartjes) and hasattr(kaartjes[-1], 'heading'):
            # er waren geen kaartjes voor die competitie - meld dat
            kaartje = SimpleNamespace()
            kaartje.geen_kaartjes = True
            kaartjes.append(kaartje)

        # maak een afsluiter (wordt gebruikt in de template)
        if prev_jaar != 0:
            kaartje = SimpleNamespace()
            kaartje.einde_blok = True
            kaartjes.append(kaartje)

        eval_open_taken(self.request)

        context['kruimels'] = (
            (None, 'Beheer Vereniging'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
