# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.formats import localize
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_BK
from Competitie.models import Competitie, Regiocompetitie, Kampioenschap
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Score.operations import wanneer_ag_vastgesteld
from Taken.operations import eval_open_taken
import datetime


TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'


class CompetitieBeheerView(UserPassesTestMixin, TemplateView):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def _get_competitie_overzicht_beheerder(self, context, comp):

        context['toon_functies'] = self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

        if self.functie_nu:
            # kijk of deze rol nog iets te doen heeft
            context['rol_is_klaar'] = True

            # toon de competitie waar de functie een rol in heeft of had (BKO/RKO/RCL)
            for deelcomp in (Regiocompetitie
                             .objects
                             .filter(competitie=comp,
                                     functie=self.functie_nu)):
                deelcomp.competitie.bepaal_fase()
                if not deelcomp.is_afgesloten:
                    context['rol_is_klaar'] = False
            # for

            # toon de competitie waar de functie een rol in heeft of had (BKO/RKO/RCL)
            for deelcomp in (Kampioenschap
                             .objects
                             .filter(competitie=comp,
                                     functie=self.functie_nu)):
                deelcomp.competitie.bepaal_fase()
                if not deelcomp.is_afgesloten:
                    context['rol_is_klaar'] = False
            # for
        else:
            # toon alle competities (BB)
            context['rol_is_klaar'] = False

        context['object_list'] = list()

        context['regio_instellingen_globaal'] = True

        if self.rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True

            if not comp.klassengrenzen_vastgesteld:
                afstand_meter = int(comp.afstand)
                datum = wanneer_ag_vastgesteld(afstand_meter)
                if datum:
                    context['datum_ag_vastgesteld'] = localize(datum.date())
                context['comp_afstand'] = comp.afstand
                comp.url_ag_vaststellen = reverse('CompBeheer:ag-vaststellen-afstand',
                                                  kwargs={'afstand': comp.afstand})

            context['planning_deelkamps'] = (Kampioenschap
                                             .objects
                                             .filter(competitie=comp,
                                                     deel=DEEL_BK)
                                             .select_related('competitie')
                                             .order_by('competitie__afstand'))
            for obj in context['planning_deelkamps']:
                obj.titel = 'Planning'
                obj.tekst = 'Landelijke planning voor deze competitie.'
                obj.url = reverse('CompLaagBond:planning',
                                  kwargs={'deelkamp_pk': obj.pk})
            # for

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            # laat alle teams zien, ook de teams die nog niet af zijn of nog niet in een poule zitten
            # vanaf fase F laten we dit niet meer zien en komen de RK Teams in beeld
            if 'B' <= comp.fase_teams <= 'F':
                context['tekst_regio_teams_alle'] = "Alle aangemelde teams voor de regio teamcompetitie"
                context['url_regio_teams_alle'] = reverse('CompLaagRegio:regio-teams-alle',
                                                          kwargs={'comp_pk': comp.pk,
                                                                  'subset': 'auto'})

        if comp.fase_teams == 'J' and not comp.klassengrenzen_vastgesteld_rk_bk and self.rol_nu == Rollen.ROL_BKO:
            context['tekst_klassengrenzen_rk_bk_vaststellen'] = "Open inschrijving RK teams sluiten en de klassengrenzen voor het RK teams en BK teams vaststellen."
            context['url_klassengrenzen_rk_bk_vaststellen'] = reverse('CompBeheer:klassengrenzen-vaststellen-rk-bk-teams',
                                                                      kwargs={'comp_pk': comp.pk})

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            if comp.fase_teams < 'L':
                context['tekst_rayon_teams_alle'] = "Alle aangemelde teams voor de rayonkampioenschappen teams"
                context["url_rayon_teams_alle"] = reverse('CompLaagRayon:rayon-teams-alle',
                                                          kwargs={'comp_pk': comp.pk,
                                                                  'subset': 'auto'})

        if self.rol_nu == Rollen.ROL_RCL:
            toon_handmatige_ag = False
            context['toon_clusters'] = True
            context['planning_deelcomp'] = (Regiocompetitie
                                            .objects
                                            .filter(competitie=comp,
                                                    functie=self.functie_nu,
                                                    is_afgesloten=False)
                                            .select_related('nhb_regio',
                                                            'competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning Regio %s' % obj.nhb_regio.regio_nr
                obj.tekst = 'Planning van de wedstrijden voor deze competitie.'
                obj.url = reverse('CompLaagRegio:regio-planning',
                                  kwargs={'deelcomp_pk': obj.pk})

                if obj.regio_organiseert_teamcompetitie and 'F' <= comp.fase_teams <= 'G':
                    obj.titel_team_ronde = "Team Ronde"
                    obj.tekst_team_ronde = "Stel de team punten vast en zet de teamcompetitie door naar de volgende ronde."
                    obj.url_team_ronde = reverse('CompLaagRegio:start-volgende-team-ronde',
                                                 kwargs={'deelcomp_pk': obj.pk})

                obj.tekst_scores = "Scores invoeren en aanpassen voor %s voor deze competitie." % obj.nhb_regio.naam
                obj.url_scores = reverse('CompScores:scores-rcl',
                                         kwargs={'deelcomp_pk': obj.pk})

                if obj.regio_organiseert_teamcompetitie:
                    obj.tekst_regio_teams = "Teams voor de regiocompetitie inzien voor deze competitie."
                    obj.url_regio_teams = reverse('CompLaagRegio:regio-teams',
                                                  kwargs={'deelcomp_pk': obj.pk})

                    # poules kaartje alleen het head-to-head puntenmodel gekozen is
                    if obj.heeft_poules_nodig():
                        obj.tekst_poules = "Poules voor directe teamwedstrijden tussen teams in deze regiocompetitie."
                        obj.url_poules = reverse('CompLaagRegio:regio-poules',
                                                 kwargs={'deelcomp_pk': obj.pk})

                    toon_handmatige_ag = True

                comp.regio_begin_fase_D = obj.begin_fase_D
            # for

            if comp.fase_teams <= 'F':
                comp.url_regio_instellingen = reverse('CompLaagRegio:regio-instellingen',
                                                      kwargs={'comp_pk': comp.pk,
                                                              'regio_nr': self.functie_nu.nhb_regio.regio_nr})

                if toon_handmatige_ag:
                    comp.url_regio_handmatige_ag = reverse('CompLaagRegio:regio-ag-controle',
                                                           kwargs={'comp_pk': comp.pk,
                                                                   'regio_nr': self.functie_nu.nhb_regio.regio_nr})

            if comp.is_open_voor_inschrijven():
                comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-regio',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'regio_pk': self.functie_nu.nhb_regio.pk})

            if comp.fase_indiv == 'G':      # teams follows
                context['afsluiten_deelcomp'] = (Regiocompetitie
                                                 .objects
                                                 .filter(competitie=comp,
                                                         functie=self.functie_nu,
                                                         is_afgesloten=False)
                                                 .select_related('nhb_regio', 'competitie'))
                for obj in context['afsluiten_deelcomp']:
                    obj.titel = 'Sluit Regiocompetitie'
                    obj.tekst = 'Bevestig eindstand %s voor de %s.' % (obj.nhb_regio.naam, obj.competitie.beschrijving)
                    obj.url_afsluiten = reverse('CompLaagRegio:afsluiten-regiocomp',
                                                kwargs={'deelcomp_pk': obj.pk})
                # for

            context['regio_instellingen_globaal'] = False

            if context['rol_is_klaar']:
                context['url_medailles'] = reverse('CompLaagRegio:medailles',
                                                   kwargs={'regio': self.functie_nu.nhb_regio.regio_nr})

        elif self.rol_nu == Rollen.ROL_RKO:
            deelkamps = (Kampioenschap
                         .objects
                         .select_related('nhb_rayon',
                                         'competitie')
                         .filter(competitie=comp,
                                 functie=self.functie_nu,
                                 is_afgesloten=False))
            if len(deelkamps):
                deelkamp = deelkamps[0]
                context['planning_deelkamps'] = [deelkamp]

                deelkamp.titel = 'Planning %s' % deelkamp.nhb_rayon.naam
                deelkamp.tekst = 'Planning voor %s voor deze competitie.' % deelkamp.nhb_rayon.naam
                deelkamp.url = reverse('CompLaagRayon:rayon-planning', kwargs={'deelkamp_pk': deelkamp.pk})

                deelkamp.tekst_rayon_teams = "Aangemelde teams voor de Rayonkampioenschappen in Rayon %s." % deelkamp.nhb_rayon.rayon_nr
                deelkamp.url_rayon_teams = reverse('CompLaagRayon:rayon-teams',
                                                   kwargs={'deelkamp_pk': deelkamp.pk})

                # geeft de RKO de mogelijkheid om de deelnemerslijst voor het RK te bewerken
                context['url_lijst_rk'] = reverse('CompLaagRayon:lijst-rk',
                                                  kwargs={'deelkamp_pk': deelkamp.pk})

                context['url_limieten_rk'] = reverse('CompLaagRayon:rayon-limieten',
                                                     kwargs={'deelkamp_pk': deelkamp.pk})

            if comp.is_open_voor_inschrijven():
                comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-rayon',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'rayon_pk': self.functie_nu.nhb_rayon.pk})

        elif self.rol_nu == Rollen.ROL_BKO:
            deelkamps = (Kampioenschap
                         .objects
                         .filter(competitie=comp,
                                 functie=self.functie_nu,
                                 is_afgesloten=False)
                         .select_related('competitie'))

            if len(deelkamps) > 0:
                deelkamp = deelkamps[0]
                context['planning_deelkamps'] = [deelkamp]

                deelkamp.titel = 'Planning'
                deelkamp.tekst = 'Landelijke planning voor deze competitie.'
                deelkamp.url = reverse('CompLaagBond:planning', kwargs={'deelkamp_pk': deelkamp.pk})

                # geef de BKO de mogelijkheid om
                # - de regiocompetitie door te zetten naar de rayonkampioenschappen
                # - de RK door te zetten naar de BK
                if comp.fase_indiv == 'G':      # teams volgt
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-naar-rk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s doorzetten naar de volgende fase (regio naar RK)' % comp.beschrijving
                    context['bko_doorzetten'] = comp

                elif comp.fase_indiv == 'L':
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-naar-bk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s individueel doorzetten naar de volgende fase (RK naar BK)' % comp.beschrijving
                    context['bko_doorzetten'] = comp

                elif 'N' <= comp.fase_indiv <= 'O':
                    # BK prep fase
                    # geeft de BKO de mogelijkheid om de deelnemerslijst voor het BK te bewerken
                    context['url_selectie_bk'] = reverse('CompLaagBond:bk-selectie',
                                                         kwargs={'deelkamp_pk': deelkamp.pk})

                    context['url_limieten_bk'] = reverse('CompLaagBond:wijzig-limieten',
                                                         kwargs={'deelkamp_pk': deelkamp.pk})

                elif comp.fase_indiv == 'P':
                    # bevestig uitslag BK
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-voorbij-bk',       # TODO: rename
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s uitslag BK bevestigen' % comp.beschrijving
                    context['bko_doorzetten'] = comp

                # teams
                if comp.fase_teams == 'L':
                    # TODO: apart kaartje maken voor teams
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-naar-bk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s teams doorzetten naar de volgende fase (RK naar BK)' % comp.beschrijving
                    context['bko_doorzetten'] = comp

                # TODO: meer opties voor teamcompetitie

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        comp.bepaal_fase()                     # zet comp.fase
        comp.bepaal_openbaar(self.rol_nu)      # zet comp.is_openbaar

        comp.einde_fase_F = comp.einde_fase_F + datetime.timedelta(days=7)
        comp.einde_fase_G = comp.einde_fase_F + datetime.timedelta(days=1)
        comp.einde_fase_K = comp.begin_fase_L_indiv - datetime.timedelta(days=14)
        comp.einde_fase_M = comp.einde_fase_L_indiv + datetime.timedelta(days=7)

        if comp.is_open_voor_inschrijven():
            comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-alles',
                                              kwargs={'comp_pk': comp.pk})

        self._get_competitie_overzicht_beheerder(context, comp)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if comp.fase_indiv >= 'C':
            context['url_uitslagen'] = reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk})

        context['url_tijdlijn'] = reverse('Competitie:tijdlijn', kwargs={'comp_pk': comp.pk})

        eval_open_taken(self.request)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:beheer', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Beheer')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
