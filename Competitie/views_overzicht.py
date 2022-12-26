# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.urls import reverse
from django.http import Http404
from django.views.generic import View
from django.utils.formats import localize
from Competitie.models import get_competitie_boog_typen, LAAG_REGIO, LAAG_BK, Competitie, DeelCompetitie
from Functie.models import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Score.operations import wanneer_ag_vastgesteld
from Sporter.models import SporterBoog
from Taken.operations import eval_open_taken
import datetime


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_HWL = 'competitie/overzicht-hwl.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'


class CompetitieOverzichtView(View):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None

    def _get_competitie_overzicht_beheerder(self, request, context, comp):

        kan_beheren = False

        context['huidige_rol'] = rol_get_beschrijving(request)
        context['toon_functies'] = self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

        if self.functie_nu:
            # kijk of deze rol nog iets te doen heeft
            context['rol_is_klaar'] = True

            # toon de competitie waar de functie een rol in heeft of had (BKO/RKO/RCL)
            for deelcomp in (DeelCompetitie
                             .objects
                             .filter(competitie=comp,
                                     functie=self.functie_nu)):
                kan_beheren = True
                deelcomp.competitie.bepaal_fase()
                if not deelcomp.is_afgesloten:
                    context['rol_is_klaar'] = False
            # for
        else:
            # toon alle competities (IT/BB)
            context['rol_is_klaar'] = False

        context['object_list'] = list()

        context['regio_instellingen_globaal'] = True

        if self.rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True
            kan_beheren = True

            if not comp.klassengrenzen_vastgesteld:
                afstand_meter = int(comp.afstand)
                datum = wanneer_ag_vastgesteld(afstand_meter)
                if datum:
                    context['datum_ag_vastgesteld'] = localize(datum.date())
                context['comp_afstand'] = comp.afstand
                comp.url_ag_vaststellen = reverse('CompBeheer:ag-vaststellen-afstand',
                                                  kwargs={'afstand': comp.afstand})

            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(competitie=comp,
                                                    laag=LAAG_BK)
                                            .select_related('competitie')
                                            .order_by('competitie__afstand'))
            for obj in context['planning_deelcomp']:
                kan_beheren = True

                obj.titel = 'Planning'
                obj.tekst = 'Landelijke planning voor deze competitie.'
                obj.url = reverse('CompLaagBond:bond-planning',
                                  kwargs={'deelcomp_pk': obj.pk})
            # for

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            # laat alle teams zien, ook de teams die nog niet af zijn of nog niet in een poule zitten
            # vanaf fase E laten we dit niet meer zien en komen de RK Teams in beeld
            if 'B' <= comp.fase <= 'E':
                context['tekst_regio_teams_alle'] = "Alle aangemelde teams voor de regio teamcompetitie"
                context['url_regio_teams_alle'] = reverse('CompLaagRegio:regio-teams-alle',
                                                          kwargs={'comp_pk': comp.pk,
                                                                  'subset': 'auto'})

        if comp.fase == 'J' and not comp.klassengrenzen_vastgesteld_rk_bk and self.rol_nu == Rollen.ROL_BKO:
            context['tekst_klassengrenzen_rk_bk_vaststellen'] = "Open inschrijving RK teams sluiten en de klassengrenzen voor het RK teams en BK teams vaststellen."
            context['url_klassengrenzen_rk_bk_vaststellen'] = reverse('CompLaagRayon:klassengrenzen-vaststellen-rk-bk-teams',
                                                                      kwargs={'comp_pk': comp.pk})

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            if comp.fase < 'L':
                context['tekst_rayon_teams_alle'] = "Alle aangemelde teams voor de rayonkampioenschappen teams"
                context["url_rayon_teams_alle"] = reverse('CompLaagRayon:rayon-teams-alle',
                                                          kwargs={'comp_pk': comp.pk,
                                                                  'subset': 'auto'})

        if self.rol_nu == Rollen.ROL_RCL:
            toon_handmatige_ag = False
            context['toon_clusters'] = True
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(competitie=comp,
                                                    functie=self.functie_nu,
                                                    is_afgesloten=False)
                                            .select_related('nhb_regio', 'competitie'))
            for obj in context['planning_deelcomp']:
                kan_beheren = True

                obj.titel = 'Planning Regio %s' % obj.nhb_regio.regio_nr
                obj.tekst = 'Planning van de wedstrijden voor deze competitie.'
                obj.url = reverse('CompLaagRegio:regio-planning',
                                  kwargs={'deelcomp_pk': obj.pk})

                if obj.regio_organiseert_teamcompetitie and 'E' <= comp.fase <= 'F':
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

                comp.regio_einde_teams_aanmaken = obj.einde_teams_aanmaken
            # for

            if comp.fase <= 'F':
                comp.url_regio_instellingen = reverse('CompLaagRegio:regio-instellingen',
                                                      kwargs={'comp_pk': comp.pk,
                                                              'regio_nr': self.functie_nu.nhb_regio.regio_nr})

                if toon_handmatige_ag:
                    comp.url_regio_handmatige_ag = reverse('CompLaagRegio:regio-ag-controle',
                                                           kwargs={'comp_pk': comp.pk,
                                                                   'regio_nr': self.functie_nu.nhb_regio.regio_nr})

            if 'B' <= comp.fase <= 'E':
                comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-regio',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'regio_pk': self.functie_nu.nhb_regio.pk})

            if comp.fase >= 'E':
                context['afsluiten_deelcomp'] = (DeelCompetitie
                                                 .objects
                                                 .filter(competitie=comp,
                                                         functie=self.functie_nu,
                                                         is_afgesloten=False)
                                                 .select_related('nhb_regio', 'competitie'))
                for obj in context['afsluiten_deelcomp']:
                    kan_beheren = True

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
            deelcomp_rks = (DeelCompetitie
                            .objects
                            .select_related('nhb_rayon', 'competitie')
                            .filter(competitie=comp,
                                    functie=self.functie_nu,
                                    is_afgesloten=False))
            if len(deelcomp_rks):
                kan_beheren = True

                deelcomp_rk = deelcomp_rks[0]

                deelcomp_rk.titel = 'Planning %s' % deelcomp_rk.nhb_rayon.naam
                deelcomp_rk.tekst = 'Planning voor %s voor deze competitie.' % deelcomp_rk.nhb_rayon.naam
                deelcomp_rk.url = reverse('CompLaagRayon:rayon-planning',
                                          kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

                deelcomp_rk.tekst_rayon_teams = "Aangemelde teams voor de Rayonkampioenschappen in Rayon %s." % deelcomp_rk.nhb_rayon.rayon_nr
                deelcomp_rk.url_rayon_teams = reverse('CompLaagRayon:rayon-teams',
                                                      kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

                context['planning_deelcomp'] = [deelcomp_rk, ]

                # geeft de RKO de mogelijkheid om de deelnemerslijst voor het RK te bewerken
                context['url_lijst_rk'] = reverse('CompLaagRayon:lijst-rk',
                                                  kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

                context['url_limieten_rk'] = reverse('CompLaagRayon:rayon-limieten',
                                                     kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

            if 'B' <= comp.fase <= 'E':
                comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-rayon',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'rayon_pk': self.functie_nu.nhb_rayon.pk})

        elif self.rol_nu == Rollen.ROL_BKO:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(competitie=comp,
                                                    functie=self.functie_nu,
                                                    is_afgesloten=False)
                                            .select_related('competitie'))
            for obj in context['planning_deelcomp']:
                kan_beheren = True

                obj.titel = 'Planning'
                obj.tekst = 'Landelijke planning voor deze competitie.'
                obj.url = reverse('CompLaagBond:bond-planning',
                                  kwargs={'deelcomp_pk': obj.pk})

                # geef de BKO de mogelijkheid om
                # - de regiocompetitie door te zetten naar de rayonkampioenschappen
                # - de RK door te zetten naar de BK
                if 'E' <= comp.fase <= 'G':
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-naar-rk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s doorzetten naar de volgende fase (Regio naar RK)' % comp.beschrijving
                    context['bko_doorzetten'] = comp
                elif 'M' <= comp.fase < 'P':
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-naar-bk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s doorzetten naar de volgende fase (RK naar BK)' % comp.beschrijving
                    context['bko_doorzetten'] = comp
                elif comp.fase == 'R':
                    comp.url_doorzetten = reverse('CompBeheer:bko-doorzetten-voorbij-bk',
                                                  kwargs={'comp_pk': comp.pk})
                    comp.titel_doorzetten = '%s doorzetten voorbij het BK' % comp.beschrijving
                    context['bko_doorzetten'] = comp
            # for

        if kan_beheren:
            template_name = TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER
        else:
            template_name = TEMPLATE_COMPETITIE_OVERZICHT

        return template_name

    def _get_competitie_overzicht_hwl(self, request, context, comp):

        context['huidige_rol'] = rol_get_beschrijving(request)

        # haal zowel de 18m als 25m deelcompetities op in de regio van de HWL
        context['planning_deelcomp'] = (DeelCompetitie
                                        .objects
                                        .filter(competitie=comp,
                                                laag=LAAG_REGIO,
                                                is_afgesloten=False,
                                                nhb_regio=self.functie_nu.nhb_ver.regio))

        for deelcomp in context['planning_deelcomp']:
            comp.regio_einde_teams_aanmaken = deelcomp.einde_teams_aanmaken
        # for

        comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-regio',
                                          kwargs={'comp_pk': comp.pk,
                                                  'regio_pk': self.functie_nu.nhb_ver.regio.pk})

        return TEMPLATE_COMPETITIE_OVERZICHT_HWL

    def _get_competitie_overzicht_schutter_bezoeker(self, context, comp):
        # let op! Niet alleen voor schutter, maar ook voor gebruiker/anon

        if comp.fase >= 'B':
            context['toon_uitslagen'] = True

        if self.rol_nu == Rollen.ROL_SPORTER:
            # TODO: wedstrijdkalender toevoegen
            pass

        return TEMPLATE_COMPETITIE_OVERZICHT

    @staticmethod
    def _get_uitslagen(context, comp, request):

        # kijk of de uitslagen klaar zijn om te tonen
        context['toon_uitslagen'] = (comp.fase >= 'B')      # inschrijving is open

        wed_boog = 'r'

        if request.user.is_authenticated:
            # als deze sporter ingeschreven is voor de competitie, pak dan het boogtype waarmee hij ingeschreven is

            # kies de eerste wedstrijdboog uit de voorkeuren van sporter
            comp_boogtypen = get_competitie_boog_typen(comp)
            boog_pks = [boogtype.pk for boogtype in comp_boogtypen]

            all_bogen = (SporterBoog
                         .objects
                         .filter(sporter__account=request.user,
                                 voor_wedstrijd=True,
                                 boogtype__pk__in=boog_pks)
                         .order_by('boogtype__volgorde'))

            if all_bogen.count():
                wed_boog = all_bogen[0].boogtype.afkorting.lower()

            # TODO: zoek ook het team type van het team waarin hij geplaatst is
            # team_type = wed_boog

        team_type = list(comp.teamtypen.order_by('volgorde').values_list('afkorting', flat=True))[0].lower()    # r/r2

        context['url_regio_indiv'] = reverse('CompUitslagen:uitslagen-regio-indiv',
                                             kwargs={'comp_pk': comp.pk,
                                                     'zes_scores': 'alle',
                                                     'comp_boog': wed_boog})
        context['url_regio_teams'] = reverse('CompUitslagen:uitslagen-regio-teams',
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': team_type})
        context['url_rayon_indiv'] = reverse('CompUitslagen:uitslagen-rayon-indiv',
                                             kwargs={'comp_pk': comp.pk,
                                                     'comp_boog': wed_boog})
        context['url_rayon_teams'] = reverse('CompUitslagen:uitslagen-rayon-teams',
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': team_type})
        context['url_bond'] = reverse('CompUitslagen:uitslagen-bond',
                                      kwargs={'comp_pk': comp.pk,
                                              'comp_boog': wed_boog})

        tussen_eind = "Tussen" if comp.fase < 'G' else "Eind"
        context['text_regio_indiv'] = tussen_eind + 'stand voor de regiocompetitie individueel'
        context['text_regio_teams'] = tussen_eind + 'stand voor de regiocompetitie teams'

        tussen_eind = "Tussen" if comp.fase <= 'N' else "Eind"
        context['text_rayon_indiv'] = tussen_eind + 'stand voor de rayonkampioenschappen individueel'
        context['text_rayon_teams'] = tussen_eind + 'stand voor de rayonkampioenschappen teams'

        context['text_bond'] = 'Tussenstand voor de landelijke bondskampioenschappen'

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        self.rol_nu, self.functie_nu = rol_get_huidige_functie(request)

        context = dict()

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()                     # zet comp.fase
        comp.bepaal_openbaar(self.rol_nu)      # zet comp.is_openbaar

        comp.einde_fase_F = comp.laatst_mogelijke_wedstrijd + datetime.timedelta(days=7)
        comp.einde_fase_G = comp.einde_fase_F + datetime.timedelta(days=1)
        comp.einde_fase_K = comp.rk_eerste_wedstrijd - datetime.timedelta(days=14)
        comp.einde_fase_M = comp.rk_laatste_wedstrijd + datetime.timedelta(days=7)

        if 'B' <= comp.fase <= 'E':
            comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-alles',
                                              kwargs={'comp_pk': comp.pk})

        context['comp'] = comp

        self._get_uitslagen(context, comp, request)

        # afhankelijk van de huidige functie vs de competitie leveren we 2 pagina's:
        #   - beheerder
        #   - bezoeker
        template = None

        if self.rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            if self.functie_nu and self.functie_nu.comp_type == comp.afstand:
                # BKO/RKO/RCL van deze specifieke competitie
                template = self._get_competitie_overzicht_beheerder(request, context, comp)
                eval_open_taken(request)

        elif self.rol_nu == Rollen.ROL_BB:
            template = self._get_competitie_overzicht_beheerder(request, context, comp)
            eval_open_taken(request)

        elif self.rol_nu == Rollen.ROL_HWL:
            template = self._get_competitie_overzicht_hwl(request, context, comp)
            eval_open_taken(request)

        if not template:
            template = self._get_competitie_overzicht_schutter_bezoeker(context, comp)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, comp.beschrijving.replace(' competitie', ''))
        )

        menu_dynamics(self.request, context)
        return render(request, template, context)


# end of file
