# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie, CompetitieKlasse, KampioenschapTeam
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie


TEMPLATE_COMPRAYON_KLASSENGRENZEN_TEAMS_VASTSTELLEN = 'comprayon/bko-klassengrenzen-vaststellen-rk-bk-teams.dtl'


class KlassengrenzenTeamsVaststellenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO de status van een RK selectie aanpassen """

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

        teamtype2wkl = dict()       # [team_type.pk] = list(CompetitieKlasse)
        for rk_wkl in (CompetitieKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .select_related('team',
                                       'team__team_type')
                       .order_by('team__volgorde')):

            teamtype_pk = rk_wkl.team.team_type.pk
            if teamtype_pk not in teamtype_pks:
                teamtypes.append(rk_wkl.team.team_type)
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

        for rk_team in (KampioenschapTeam
                        .objects
                        .filter(deelcompetitie__competitie=comp)
                        .select_related('team_type')
                        .annotate(sporter_count=Count('tijdelijke_schutters'))
                        .order_by('team_type__volgorde',
                                  '-aanvangsgemiddelde')):

            if rk_team.aanvangsgemiddelde < 0.001:
                print('geen ag voor rk_team %s' % rk_team)
            else:
                team_type_pk = rk_team.team_type.pk
                teamtype2sterktes[team_type_pk].append(rk_team.aanvangsgemiddelde)
        # for

        return teamtypes, teamtype2wkl, teamtype2sterktes

    def _bepaal_klassengrenzen(self, comp):
        tts, tt2wkl, tt2sterktes = self._tel_rk_teams(comp)

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        grenzen = list()

        for tt in tts:
            klassen = tt2wkl[tt.pk]
            sterktes = tt2sterktes[tt.pk]
            count = len(sterktes)

            aantal_klassen = len(klassen)
            step = int(count / aantal_klassen)
            if count:
                step = max(step, 1)     # ensure at least 1
            index = 0

            klassen_lijst = list()
            for klasse in klassen:
                min_ag = 0.0
                aantal_klassen -= 1

                if aantal_klassen == 0:
                    # laatste klasse = geen ondergrens
                    step = count - index
                    min_ag_str = ""     # toon n.v.t.
                else:
                    index += step
                    if index <= count:
                        min_ag = sterktes[index - 1]

                    min_ag_str = "%05.1f" % (min_ag * aantal_pijlen)
                    min_ag_str = min_ag_str.replace('.', ',')

                tup = (klasse.team.beschrijving, step, min_ag, min_ag_str)
                klassen_lijst.append(tup)
            # for

            tup = (len(klassen) + 1, tt.beschrijving, count, klassen_lijst)
            grenzen.append(tup)
        # for

        return grenzen

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

        if comp.fase != 'J':
            raise Http404('Competitie niet in de juist fase')

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        context['grenzen'] = self._bepaal_klassengrenzen(comp)

        context['url_vaststellen'] = reverse('CompRayon:klassengrenzen-vaststellen-rk-bk-teams',
                                             kwargs={'comp_pk': comp.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
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

        if comp.fase != 'J':
            raise Http404('Competitie niet in de juist fase')

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        # vul de klassengrenzen in voor RK/BK  teams

        grenzen = self._bepaal_klassengrenzen(comp)

        beschrijving2klasse = dict()

        for klasse in (CompetitieKlasse
                       .objects
                       .exclude(team=None)
                       .select_related('team')
                       .filter(is_voor_teams_rk_bk=True,
                               competitie=comp)):
            beschrijving2klasse[klasse.team.beschrijving] = klasse
        # for

        teamtype_pk2klassen = dict()        # hoogste klasse eerst

        # neem de voorgestelde klassengrenzen over
        for _, _, _, klassen_lijst in grenzen:
            for beschrijving, _, min_ag, _ in klassen_lijst:
                try:
                    klasse = beschrijving2klasse[beschrijving]
                except KeyError:
                    raise Http404('Kan competitie klasse %s niet vinden' % repr(beschrijving))

                klasse.min_ag = min_ag
                klasse.save(update_fields=['min_ag'])

                teamtype_pk = klasse.team.team_type.pk
                try:
                    teamtype_pk2klassen[teamtype_pk].append(klasse)
                except KeyError:
                    teamtype_pk2klassen[teamtype_pk] = [klasse]
            # for
        # for

        # plaats elk RK team in een wedstrijdklasse
        for team in (KampioenschapTeam
                     .objects
                     .filter(deelcompetitie__competitie=comp)
                     .annotate(sporter_count=Count('gekoppelde_schutters'))):

            if 3 <= team.sporter_count <= 4:
                # dit is een volledig team
                klassen = teamtype_pk2klassen[team.team_type.pk]

                for klasse in klassen:
                    if team.aanvangsgemiddelde >= klasse.min_ag:
                        team.klasse = klasse
                        break       # from the for
                # for
            else:
                team.klasse = None

            team.save(update_fields=['klasse'])
        # for

        # zet de competitie door naar fase K
        comp.klassengrenzen_vastgesteld_rk_bk = True
        comp.save(update_fields=['klassengrenzen_vastgesteld_rk_bk'])

        url = reverse('Competitie:overzicht',
                      kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)

# end of file
