# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie, CompetitieTeamKlasse, KampioenschapTeam
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics


TEMPLATE_COMPRAYON_KLASSENGRENZEN_TEAMS_VASTSTELLEN = 'complaagrayon/bko-klassengrenzen-vaststellen-rk-bk-teams.dtl'


class KlassengrenzenTeamsVaststellenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de teams klassengrenzen voor het RK en BK vaststellen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_KLASSENGRENZEN_TEAMS_VASTSTELLEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

    @staticmethod
    def _tel_rk_teams(comp):
        """ Verdeel de ingeschreven (en complete) teams van elk team type over de beschikbare
            team wedstrijdklassen, door de grenzen tussen de klassen te bepalen.
        """

        teamtype_pks = list()
        teamtypes = list()

        teamtype2wkl = dict()       # [team_type.pk] = list(CompetitieTeamKlasse)
        for rk_wkl in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .select_related('team_type')
                       .order_by('volgorde')):

            teamtype_pk = rk_wkl.team_type.pk
            if teamtype_pk not in teamtype_pks:
                teamtypes.append(rk_wkl.team_type)
                teamtype_pks.append(teamtype_pk)

            try:
                teamtype2wkl[teamtype_pk].append(rk_wkl)
            except KeyError:
                teamtype2wkl[teamtype_pk] = [rk_wkl]
        # for

        teamtype2sterktes = dict()     # [team_type.pk] = [sterkte, sterkte, ..]
        for pk in teamtype2wkl.keys():
            teamtype2sterktes[pk] = list()
        # for

        niet_compleet_team = False

        for rk_team in (KampioenschapTeam
                        .objects
                        .filter(deelcompetitie__competitie=comp)
                        .select_related('team_type')
                        .annotate(sporter_count=Count('tijdelijke_schutters'))
                        .order_by('team_type__volgorde',
                                  '-aanvangsgemiddelde')):

            if rk_team.aanvangsgemiddelde < 0.001:
                niet_compleet_team = True
            else:
                team_type_pk = rk_team.team_type.pk
                try:
                    teamtype2sterktes[team_type_pk].append(rk_team.aanvangsgemiddelde)
                except KeyError:
                    # abnormal: unexpected team type used in RK team
                    pass
        # for

        return teamtypes, teamtype2wkl, teamtype2sterktes, niet_compleet_team

    def _bepaal_klassengrenzen(self, comp):
        tts, tt2wkl, tt2sterktes, niet_compleet_team = self._tel_rk_teams(comp)

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        grenzen = list()

        if not niet_compleet_team:
            for tt in tts:
                klassen = tt2wkl[tt.pk]
                sterktes = tt2sterktes[tt.pk]
                count = len(sterktes)
                index = 0

                aantal_klassen = len(klassen)
                aantal_per_klasse = count / aantal_klassen

                ophoog_factor = 0.4
                ophoog_step = 1.0 / aantal_klassen     # 5 klassen --> 0.2 --> +0.4 +0.2 +0.0 -0.2

                klassen_lijst = list()
                for klasse in klassen:
                    min_ag = 0.0

                    if len(klassen_lijst) + 1 == aantal_klassen:
                        # laatste klasse = geen ondergrens
                        step = count - index
                        min_ag_str = ""     # toon n.v.t.
                    else:
                        step = round(aantal_per_klasse + ophoog_factor)
                        index += step
                        ophoog_factor -= ophoog_step
                        if index <= count and count > 0:
                            min_ag = sterktes[index - 1]

                        min_ag_str = "%05.1f" % (min_ag * aantal_pijlen)
                        min_ag_str = min_ag_str.replace('.', ',')

                    tup = (klasse.beschrijving, step, min_ag, min_ag_str)
                    klassen_lijst.append(tup)
                # for

                tup = (len(klassen) + 1, tt.beschrijving, count, klassen_lijst)
                grenzen.append(tup)
            # for

        return grenzen, niet_compleet_team

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
        comp.bepaal_fase()

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        if comp.fase != 'J':
            raise Http404('Competitie niet in de juiste fase')

        context['grenzen'], context['niet_compleet_team'] = self._bepaal_klassengrenzen(comp)

        if context['niet_compleet_team']:
            context['url_terug'] = reverse('Competitie:overzicht',
                                           kwargs={'comp_pk': comp.pk})

        context['url_vaststellen'] = reverse('CompLaagRayon:klassengrenzen-vaststellen-rk-bk-teams',
                                             kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ hanteer de bevestiging van de BKO om de klassengrenzen voor de RK/BK teams vast te stellen
            volgens het voorstel dat gepresenteerd was.
        """

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        if comp.fase != 'J':
            raise Http404('Competitie niet in de juiste fase')

        # vul de klassengrenzen in voor RK/BK  teams

        grenzen, niet_compleet_team = self._bepaal_klassengrenzen(comp)

        if niet_compleet_team:
            raise Http404('Niet alle teams zijn compleet')

        beschrijving2team_klasse = dict()

        for team_klasse in (CompetitieTeamKlasse
                            .objects
                            .filter(is_voor_teams_rk_bk=True,
                                    competitie=comp)
                            .select_related('team_type')):
            beschrijving2team_klasse[team_klasse.beschrijving] = team_klasse
        # for

        teamtype_pk2klassen = dict()        # hoogste klasse eerst

        # neem de voorgestelde klassengrenzen over
        for _, _, _, klassen_lijst in grenzen:
            for beschrijving, _, min_ag, _ in klassen_lijst:
                try:
                    team_klasse = beschrijving2team_klasse[beschrijving]
                except KeyError:
                    raise Http404('Kan competitie klasse %s niet vinden' % repr(beschrijving))

                team_klasse.min_ag = min_ag
                team_klasse.save(update_fields=['min_ag'])

                teamtype_pk = team_klasse.team_type.pk
                try:
                    teamtype_pk2klassen[teamtype_pk].append(team_klasse)
                except KeyError:
                    teamtype_pk2klassen[teamtype_pk] = [team_klasse]
            # for
        # for

        # plaats elk RK team in een wedstrijdklasse
        for team in (KampioenschapTeam
                     .objects
                     .filter(deelcompetitie__competitie=comp)
                     .annotate(sporter_count=Count('gekoppelde_schutters'))):

            team.team_klasse = None
            if 3 <= team.sporter_count <= 4:
                # dit is een volledig team
                try:
                    klassen = teamtype_pk2klassen[team.team_type.pk]
                except KeyError:
                    # onverwacht team type (ignore, avoid crash)
                    pass
                else:
                    for team_klasse in klassen:
                        if team.aanvangsgemiddelde >= team_klasse.min_ag:
                            team.team_klasse = team_klasse
                            break       # from the for
                    # for

            team.save(update_fields=['team_klasse'])
        # for

        # zet de competitie door naar fase K
        comp.klassengrenzen_vastgesteld_rk_bk = True
        comp.save(update_fields=['klassengrenzen_vastgesteld_rk_bk'])

        url = reverse('Competitie:overzicht',
                      kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)

# end of file
