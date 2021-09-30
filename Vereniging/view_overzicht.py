# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.templatetags.static import static
from Competitie.models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                               LAAG_REGIO, LAAG_RK, INSCHRIJF_METHODE_1)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Taken.taken import eval_open_taken
from Wedstrijden.models import CompetitieWedstrijd, BAAN_TYPE_EXTERN
from types import SimpleNamespace
import datetime


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

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

        context['clusters'] = ver.clusters.all()

        if self.functie_nu.nhb_ver.wedstrijdlocatie_set.exclude(baan_type=BAAN_TYPE_EXTERN).filter(zichtbaar=True).count() > 0:
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details',
                                                          kwargs={'vereniging_pk': ver.pk})

        context['url_externe_locaties'] = reverse('Vereniging:externe-locaties',
                                                  kwargs={'vereniging_pk': ver.pk})

        if self.rol_nu == Rollen.ROL_SEC or ver.regio.is_administratief:
            # SEC
            comps = list()
            deelcomps = list()
            deelcomps_rk = list()
        else:
            # HWL of WL
            context['toon_competities'] = True

            # if rol_nu == Rollen.ROL_HWL:
            #     context['toon_wedstrijdkalender'] = True

            comps = (Competitie
                     .objects
                     .filter(is_afgesloten=False)
                     .order_by('afstand',
                               'begin_jaar'))

            deelcomps = (DeelCompetitie
                         .objects
                         .filter(laag=LAAG_REGIO,
                                 competitie__is_afgesloten=False,
                                 nhb_regio=ver.regio)
                         .select_related('competitie'))

            deelcomps_rk = (DeelCompetitie
                            .objects
                            .filter(laag=LAAG_RK,
                                    competitie__is_afgesloten=False,
                                    nhb_rayon=ver.regio.rayon)
                            .select_related('competitie'))

            for deelcomp_rk in deelcomps_rk:
                if deelcomp_rk.heeft_deelnemerslijst:
                    comp = deelcomp_rk.competitie
                    comp.bepaal_fase()
                    if comp.fase == 'K':
                        # RK voorbereidende fase
                        deelcomp_rk.text_str = "Schutters van de vereniging aan-/afmelden voor het RK van de %s" % comp.beschrijving
                        deelcomp_rk.url_lijst_rk = reverse('Vereniging:lijst-rk',
                                                           kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})
            # for

            pks = (DeelcompetitieRonde
                   .objects
                   .filter(deelcompetitie__is_afgesloten=False,
                           plan__wedstrijden__vereniging=ver)
                   .values_list('plan__wedstrijden', flat=True))
            if CompetitieWedstrijd.objects.filter(pk__in=pks).count() > 0:
                context['heeft_wedstrijden'] = True

        # bepaal de volgorde waarin de kaartjes getoond worden
        # 1 - aanmelden
        # 2 - teams regio aanmelden / aanpassen
        # 3 - teams rk
        # 4 - ingeschreven
        # 5 - wie schiet waar (voor inschrijfmethode 1)
        context['kaartjes'] = kaartjes = list()
        prev_jaar = 0
        prev_afstand = 0
        for comp in comps:
            begin_jaar = comp.begin_jaar
            comp.bepaal_fase()

            if prev_jaar != begin_jaar or prev_afstand != comp.afstand:
                if len(kaartjes) and hasattr(kaartjes[-1], 'heading'):
                    # er waren geen kaartjes voor die competitie - meld dat
                    kaartje = SimpleNamespace()
                    kaartje.geen_kaartjes = True
                    kaartjes.append(kaartje)

                # nieuwe heading aanmaken
                kaartje = SimpleNamespace()
                kaartje.heading = comp.beschrijving
                kaartjes.append(kaartje)

                prev_jaar = begin_jaar
                prev_afstand = comp.afstand

            # 1 - leden aanmelden voor de competitie (niet voor de WL)
            if comp.fase < 'F' and self.rol_nu != Rollen.ROL_WL:
                kaartje = SimpleNamespace()
                kaartje.titel = "Aanmelden"
                kaartje.tekst = 'Leden aanmelden voor de %s.' % comp.beschrijving
                kaartje.url = reverse('Vereniging:leden-aanmelden', kwargs={'comp_pk': comp.pk})
                if comp.afstand == '18':
                    kaartje.img = static('plein/badge_nhb_indoor.png')
                else:
                    kaartje.img = static('plein/badge_nhb_25m1p.png')
                if comp.fase < 'B':
                    kaartje.beschikbaar_vanaf = localize(comp.begin_aanmeldingen)
                kaartjes.append(kaartje)

            for deelcomp in deelcomps:
                if deelcomp.competitie == comp:
                    if deelcomp.regio_organiseert_teamcompetitie and comp.fase == 'E' and 1 <= deelcomp.huidige_team_ronde <= 7:
                        # team invallers opgeven
                        kaartje = SimpleNamespace(
                                    titel="Team Invallers",
                                    tekst="Invallers opgeven voor ronde %s van de regiocompetitie voor de %s." % (deelcomp.huidige_team_ronde, comp.beschrijving),
                                    url=reverse('Vereniging:teams-regio-invallers', kwargs={'deelcomp_pk': deelcomp.pk}),
                                    icon='how_to_reg')
                        kaartjes.append(kaartje)
                    else:
                        # 2 - teams aanmaken
                        if deelcomp.regio_organiseert_teamcompetitie and comp.fase <= 'E':
                            kaartje = SimpleNamespace()
                            kaartje.titel = "Teams Regio"
                            kaartje.tekst = 'Verenigingsteams voor de regiocompetitie samenstellen voor de %s.' % comp.beschrijving
                            kaartje.url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
                            kaartje.icon = 'gamepad'
                            if comp.fase < 'B':
                                kaartje.beschikbaar_vanaf = localize(comp.begin_aanmeldingen)
                            kaartjes.append(kaartje)
            # for
            del deelcomp

            # 3 - teams RK
            for deelcomp_rk in deelcomps_rk:
                if deelcomp_rk.competitie == comp:
                    if 'E' <= comp.fase <= 'K' and self.rol_nu != Rollen.ROL_WL:
                        kaartje = SimpleNamespace()
                        kaartje.titel = "Teams RK"
                        kaartje.tekst = "Verenigingsteams voor de rayonkampioenschappen samenstellen voor de %s." % comp.beschrijving
                        kaartje.url = reverse('Vereniging:teams-rk', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})
                        kaartje.icon = 'api'
                        # niet beschikbaar maken tot een paar weken na de eerste regiowedstrijd
                        vanaf = comp.eerste_wedstrijd + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
                        if datetime.date.today() < vanaf:
                            kaartje.beschikbaar_vanaf = localize(vanaf)
                        kaartjes.append(kaartje)
            # for
            del deelcomp_rk

            for deelcomp in deelcomps:
                if deelcomp.competitie == comp:
                    # 4 - ingeschreven
                    if 'B' <= comp.fase <= 'F':         # vanaf RK fase niet meer tonen
                        kaartje = SimpleNamespace()
                        kaartje.titel = "Ingeschreven"
                        kaartje.tekst = "Overzicht ingeschreven leden voor de %s." % comp.beschrijving
                        kaartje.url = reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})
                        if comp.afstand == '18':
                            kaartje.img = static('plein/badge_nhb_indoor.png')
                        else:
                            kaartje.img = static('plein/badge_nhb_25m1p.png')
                        kaartjes.append(kaartje)

                    # 5 - wie schiet waar
                    if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1 and 'B' <= comp.fase <= 'F':
                        kaartje = SimpleNamespace()
                        kaartje.titel = "Wie schiet waar?"
                        kaartje.tekst = 'Overzicht gekozen schietmomenten voor de %s.' % comp.beschrijving
                        kaartje.url = reverse('Vereniging:schietmomenten', kwargs={'deelcomp_pk': deelcomp.pk})
                        kaartje.icon = 'gamepad'
                        if comp.fase < 'B':
                            kaartje.beschikbaar_vanaf = localize(comp.begin_aanmeldingen)
                        kaartjes.append(kaartje)
            # for

        # for

        eval_open_taken(self.request)

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
