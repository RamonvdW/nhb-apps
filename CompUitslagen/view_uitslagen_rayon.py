# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from BasisTypen.models import BoogType, TeamType
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Competitie.models import (LAAG_REGIO, LAAG_RK, DEELNAME_NEE,
                               Competitie, DeelCompetitie, DeelcompetitieKlasseLimiet,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog, KampioenschapTeam)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie


TEMPLATE_COMPUITSLAGEN_VERENIGING_INDIV = 'compuitslagen/uitslagen-vereniging-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_VERENIGING_TEAMS = 'compuitslagen/uitslagen-vereniging-teams.dtl'
TEMPLATE_COMPUITSLAGEN_REGIO_INDIV = 'compuitslagen/uitslagen-regio-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_REGIO_TEAMS = 'compuitslagen/uitslagen-regio-teams.dtl'
TEMPLATE_COMPUITSLAGEN_RAYON_INDIV = 'compuitslagen/uitslagen-rayon-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_RAYON_TEAMS = 'compuitslagen/uitslagen-rayon-teams.dtl'
TEMPLATE_COMPUITSLAGEN_BOND = 'compuitslagen/uitslagen-bond.dtl'


def get_sporter_regio_nr(request):
    """ Geeft het regio nummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    regio_nr = 101

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.nhb_ver:
            # HWL, WL
            regio_nr = functie_nu.nhb_ver.regio.regio_nr
        elif functie_nu.nhb_regio:
            # RCL
            regio_nr = functie_nu.nhb_regio.regio_nr
        elif functie_nu.nhb_rayon:
            # RKO
            regio = (NhbRegio
                     .objects
                     .filter(rayon=functie_nu.nhb_rayon,
                             is_administratief=False)
                     .order_by('regio_nr'))[0]
            regio_nr = regio.regio_nr
    elif rol_nu == Rollen.ROL_SPORTER:
        # sporter
        account = request.user
        if account.sporter_set.count() > 0:
            sporter = account.sporter_set.all()[0]
            if sporter.is_actief_lid and sporter.bij_vereniging:
                nhb_ver = sporter.bij_vereniging
                regio_nr = nhb_ver.regio.regio_nr

    return regio_nr


def get_sporter_rayon_nr(request):
    """ Geeft het rayon nummer van de ingelogde sporter terug,
        of 1 als er geen rayon vastgesteld kan worden
    """
    rayon_nr = 1

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.nhb_ver:
            # HWL, WL
            rayon_nr = functie_nu.nhb_ver.regio.rayon.rayon_nr
        elif functie_nu.nhb_regio:
            # RCL
            rayon_nr = functie_nu.nhb_regio.rayon.rayon_nr
        elif functie_nu.nhb_rayon:
            # RKO
            rayon_nr = functie_nu.nhb_rayon.rayon_nr
    elif rol_nu == Rollen.ROL_SPORTER:
        # sporter
        account = request.user
        if account.sporter_set.count() > 0:
            sporter = account.sporter_set.all()[0]
            if sporter.is_actief_lid and sporter.bij_vereniging:
                nhb_ver = sporter.bij_vereniging
                rayon_nr = nhb_ver.regio.rayon.rayon_nr

    return rayon_nr


def get_sporter_ver_nr(request):

    """ Geeft het vereniging nhb nummer van de ingelogde schutter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    ver_nr = -1

    if request.user.is_authenticated:
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if functie_nu and functie_nu.nhb_ver:
            # HWL, WL, SEC
            ver_nr = functie_nu.nhb_ver.ver_nr

        if ver_nr < 0:
            # pak de vereniging van de ingelogde gebruiker
            account = request.user
            if account.sporter_set.count() > 0:
                sporter = account.sporter_set.all()[0]
                if sporter.is_actief_lid and sporter.bij_vereniging:
                    ver_nr = sporter.bij_vereniging.ver_nr

    ver_nrs = list(NhbVereniging.objects.order_by('ver_nr').values_list('ver_nr', flat=True))
    if ver_nr not in ver_nrs:
        ver_nr = ver_nrs[0]

    return ver_nr


class UitslagenRayonIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen individueel """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RAYON_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                            kwargs={'comp_pk': comp.pk,
                                                    'comp_boog': boogtype.afkorting.lower(),
                                                    'rayon_nr': gekozen_rayon_nr})
        # for

        if context['comp_boog']:
            # rayon filters
            rayons = (NhbRayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.title_str = 'Rayon %s' % rayon.rayon_nr
                if rayon.rayon_nr != gekozen_rayon_nr:
                    rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                             kwargs={'comp_pk': comp.pk,
                                                     'comp_boog': comp_boog,
                                                     'rayon_nr': rayon.rayon_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['rayon'] = rayon
            # for

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

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_sporter_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, comp, rayon_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_rayon')
                        .get(laag=LAAG_RK,
                             competitie__is_afgesloten=False,
                             competitie=comp,
                             nhb_rayon__rayon_nr=rayon_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp
        deelcomp.competitie.bepaal_fase()

        wkl2limiet = dict()    # [pk] = aantal

        if deelcomp.heeft_deelnemerslijst:
            # deelnemers/reserveschutters van het RK tonen
            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .exclude(bij_vereniging__isnull=True)      # attentie gevallen
                          .exclude(deelname=DEELNAME_NEE)            # geen sporters die zich afgemeld hebben
                          .filter(deelcompetitie=deelcomp,
                                  klasse__indiv__boogtype=boogtype,
                                  volgorde__lte=48)                  # toon tot 48 sporters per klasse
                          .select_related('klasse__indiv',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('klasse__indiv__volgorde',
                                    'volgorde'))

            for limiet in (DeelcompetitieKlasseLimiet
                           .objects
                           .select_related('klasse')
                           .filter(deelcompetitie=deelcomp)):
                wkl2limiet[limiet.klasse.pk] = limiet.limiet
            # for

            context['is_lijst_rk'] = True
        else:
            # competitie is nog in de regiocompetitie fase
            context['regiocomp_nog_actief'] = True

            # sporters moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
            deelcomp_pks = (DeelCompetitie
                            .objects
                            .filter(laag=LAAG_REGIO,
                                    competitie__is_afgesloten=False,
                                    competitie=comp,
                                    nhb_regio__rayon__rayon_nr=rayon_nr)
                            .values_list('pk', flat=True))

            deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .filter(deelcompetitie__pk__in=deelcomp_pks,
                                  klasse__indiv__boogtype=boogtype,
                                  aantal_scores__gte=comp.aantal_scores_voor_rk_deelname)
                          .select_related('klasse__indiv',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('klasse__indiv__volgorde', '-gemiddelde'))

        klasse = -1
        limiet = 24
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                try:
                    limiet = wkl2limiet[deelnemer.klasse.pk]
                except KeyError:
                    limiet = 24
            klasse = deelnemer.klasse.indiv.volgorde

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            deelnemer.geen_deelname_risico = deelnemer.sporterboog.sporter.bij_vereniging != deelnemer.bij_vereniging

            if deelcomp.heeft_deelnemerslijst:
                if deelnemer.rank > limiet:
                    deelnemer.is_reserve = True
        # for

        context['deelnemers'] = deelnemers

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenRayonTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen teams """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RAYON_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, teamtype_afkorting):
        """ filter knoppen per rayon en per competitie boog type """

        # team type filter
        teamtypen = TeamType.objects.order_by('volgorde').all()

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen

        for team in teamtypen:
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                # geen url --> knop disabled
            else:
                team.zoom_url = reverse('CompUitslagen:uitslagen-rayon-teams-n',
                                        kwargs={'comp_pk': comp.pk,
                                                'team_type': team.afkorting.lower(),
                                                'rayon_nr': gekozen_rayon_nr})
        # for

        # als het team type correct was, maak dan de rayon knopppen
        if context['teamtype']:
            # rayon filters
            rayons = (NhbRayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.title_str = 'Rayon %s' % rayon.rayon_nr
                if rayon.rayon_nr != gekozen_rayon_nr:
                    rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-teams-n',
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': teamtype_afkorting,
                                                     'rayon_nr': rayon.rayon_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['rayon'] = rayon
            # for

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

        comp.bepaal_fase()
        context['comp'] = comp

        teamtype_afkorting = kwargs['team_type'][:2]     # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_sporter_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, comp, rayon_nr, teamtype_afkorting)

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        try:
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie',
                                           'nhb_rayon')
                           .get(laag=LAAG_RK,
                                competitie=comp,
                                competitie__is_afgesloten=False,
                                nhb_rayon__rayon_nr=rayon_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp_rk'] = deelcomp_rk
        comp = deelcomp_rk.competitie
        comp.bepaal_fase()

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        rk_teams = (KampioenschapTeam
                    .objects
                    .filter(deelcompetitie=deelcomp_rk,
                            team_type=teamtype)
                    .select_related('klasse__team')
                    .order_by('klasse__team__volgorde',
                              '-aanvangsgemiddelde'))       # sterkste team eerst

        prev_klasse = ""
        rank = 0
        for team in rk_teams:
            if team.klasse != prev_klasse:
                team.break_klasse = True
                if team.klasse:
                    team.klasse_str = team.klasse.team.beschrijving
                else:
                    team.klasse_str = "%s - Nog niet ingedeeld in een wedstrijdklasse" % team.team_type.beschrijving
                prev_klasse = team.klasse
                rank = 0

            team.ver_str = str(team.vereniging)
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = team.ag_str.replace('.', ',')

            # TODO: dit scherm is zowel een kandidaat-deelnemerslijst als de uitslag

            # TODO: geen rank invullen na de cut

            rank += 1
            team.rank = rank
        # for

        context['rk_teams'] = rk_teams

        if rk_teams.count() == 0:
            context['geen_teams'] = True

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
