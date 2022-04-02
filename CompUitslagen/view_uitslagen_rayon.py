# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from NhbStructuur.models import NhbRayon
from Competitie.models import (LAAG_REGIO, LAAG_RK, DEELNAME_NEE,
                               Competitie, DeelCompetitie, DeelcompetitieKlasseLimiet,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog, KampioenschapTeam,
                               get_competitie_boog_typen, get_competitie_team_typen)
from Plein.menu import menu_dynamics
from Wedstrijden.models import CompetitieWedstrijd
from Functie.rol import Rollen, rol_get_huidige_functie


TEMPLATE_COMPUITSLAGEN_RAYON_INDIV = 'compuitslagen/uitslagen-rayon-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_RAYON_TEAMS = 'compuitslagen/uitslagen-rayon-teams.dtl'


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
        # sporter?
        account = request.user
        if account.is_authenticated:
            if account.sporter_set.count() > 0:
                sporter = account.sporter_set.all()[0]
                if sporter.is_actief_lid and sporter.bij_vereniging:
                    nhb_ver = sporter.bij_vereniging
                    rayon_nr = nhb_ver.regio.rayon.rayon_nr

    return rayon_nr


class UitslagenRayonIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen individueel """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RAYON_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype filters
        boogtypen = get_competitie_boog_typen(comp)

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = boogtype.afkorting.lower()

            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()

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
                rayon.sel = 'rayon_%s' % rayon.pk
                rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                         kwargs={'comp_pk': comp.pk,
                                                 'comp_boog': comp_boog,
                                                 'rayon_nr': rayon.rayon_nr})

                if rayon.rayon_nr == gekozen_rayon_nr:
                    context['rayon'] = rayon
                    rayon.selected = True
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

        if comp.fase == 'J':
            context['bevestig_tot_datum'] = comp.rk_eerste_wedstrijd - datetime.timedelta(days=14)

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
                        .select_related('competitie',
                                        'nhb_rayon',
                                        'plan')
                        .prefetch_related('plan__wedstrijden')
                        .get(laag=LAAG_RK,
                             competitie__is_afgesloten=False,
                             competitie=comp,
                             nhb_rayon__rayon_nr=rayon_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp
        deelcomp.competitie.bepaal_fase()           # TODO: kan weg? We hebben al comp (zie hierboven)

        # haal de planning erbij: competitieklasse --> competitiewedstrijd
        indiv2wedstrijd = dict()    # [indiv_pk] = competitiewedstrijd
        wedstrijd_pks = list(deelcomp.plan.wedstrijden.values_list('pk', flat=True))
        for wedstrijd in (CompetitieWedstrijd
                          .objects
                          .prefetch_related('indiv_klassen')
                          .select_related('locatie')
                          .filter(pk__in=wedstrijd_pks)):

            if wedstrijd.locatie:
                wedstrijd.adres_str = ", ".join(wedstrijd.locatie.adres.split('\n'))

            for indiv in wedstrijd.indiv_klassen.all():
                indiv2wedstrijd[indiv.pk] = wedstrijd
            # for
        # for

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
        curr_teller = None
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                if klasse == -1:
                    deelnemer.is_eerste_break = True
                indiv = deelnemer.klasse.indiv
                deelnemer.klasse_str = indiv.beschrijving
                try:
                    deelnemer.wedstrijd = indiv2wedstrijd[indiv.pk]
                except KeyError:
                    pass

                try:
                    limiet = wkl2limiet[deelnemer.klasse.pk]
                except KeyError:
                    limiet = 24

                curr_teller = deelnemer
                curr_teller.aantal_regels = 2

            klasse = deelnemer.klasse.indiv.volgorde

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            deelnemer.geen_deelname_risico = deelnemer.sporterboog.sporter.bij_vereniging != deelnemer.bij_vereniging

            if deelcomp.heeft_deelnemerslijst:
                if deelnemer.rank > limiet:
                    deelnemer.is_reserve = True

            curr_teller.aantal_regels += 1
        # for

        context['deelnemers'] = deelnemers

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen RK individueel')
        )

        menu_dynamics(self.request, context)
        return context


class UitslagenRayonTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen teams """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RAYON_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, teamtype_afkorting):
        """ filter knoppen per rayon en per competitie boog type """

        # team type filter
        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = get_competitie_team_typen(comp)

        for team in teamtypen:
            team.sel = 'team_' + team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                team.selected = True
            else:
                team.selected = False

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
                rayon.sel = 'rayon_%s' % rayon.rayon_nr
                rayon.selected = (rayon.rayon_nr == gekozen_rayon_nr)
                if rayon.selected:
                    context['rayon'] = rayon

                rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-teams-n',
                                         kwargs={'comp_pk': comp.pk,
                                                 'team_type': teamtype_afkorting,
                                                 'rayon_nr': rayon.rayon_nr})
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

        teamtype_afkorting = kwargs['team_type'][:3]     # afkappen voor de veiligheid

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

        # haal de planning erbij: competitieklasse --> competitiewedstrijd
        team2wedstrijd = dict()     # [team_pk] = competitiewedstrijd
        wedstrijd_pks = list(deelcomp_rk.plan.wedstrijden.values_list('pk', flat=True))
        for wedstrijd in (CompetitieWedstrijd
                          .objects
                          .prefetch_related('team_klassen')
                          .select_related('locatie')
                          .filter(pk__in=wedstrijd_pks)):

            if wedstrijd.locatie:
                wedstrijd.adres_str = ", ".join(wedstrijd.locatie.adres.split('\n'))

            for team in wedstrijd.team_klassen.all():
                team2wedstrijd[team.pk] = wedstrijd
        # for

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
        teller = None
        for team in rk_teams:
            if team.klasse != prev_klasse:
                team.break_klasse = True
                if team.klasse:
                    team.klasse_str = team.klasse.team.beschrijving
                    try:
                        team.wedstrijd = team2wedstrijd[team.klasse.team.pk]
                    except KeyError:
                        pass
                else:
                    team.klasse_str = "%s - Nog niet ingedeeld in een wedstrijdklasse" % team.team_type.beschrijving

                teller = team
                teller.aantal_regels = 2

                prev_klasse = team.klasse
                rank = 0

            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = str(team.vereniging)
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = team.ag_str.replace('.', ',')

            teller.aantal_regels += 1

            # TODO: dit scherm is zowel een kandidaat-deelnemerslijst als de uitslag

            # TODO: geen rank invullen na de cut

            rank += 1
            team.rank = rank
        # for

        context['rk_teams'] = rk_teams

        if rk_teams.count() == 0:
            context['geen_teams'] = True

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen RK teams')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
