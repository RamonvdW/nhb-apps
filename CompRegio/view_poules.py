# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import LAAG_REGIO, DeelCompetitie, RegiocompetitieTeam, RegiocompetitieTeamPoule
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from Overig.background_sync import BackgroundSync


TEMPLATE_COMPREGIO_RCL_TEAMS_POULES = 'compregio/rcl-teams-poules.dtl'
TEMPLATE_COMPREGIO_RCL_WIJZIG_POULE = 'compregio/wijzig-poule.dtl'


class RegioPoulesView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de poules hanteren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_RCL_TEAMS_POULES
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])    # afkappen voor veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio',
                                        'nhb_regio__rayon')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        context['readonly'] = readonly = (comp.fase > 'D')

        context['regio'] = deelcomp.nhb_regio

        poules = (RegiocompetitieTeamPoule
                  .objects
                  .prefetch_related('teams')
                  .filter(deelcompetitie=deelcomp)
                  .annotate(team_count=Count('teams')))

        team_pk2poule = dict()
        for poule in poules:
            poule.url_wijzig = reverse('CompRegio:wijzig-poule',
                                       kwargs={'poule_pk': poule.pk})

            for team in poule.teams.all():
                team_pk2poule[team.pk] = poule
        # for

        context['poules'] = poules

        teams = (RegiocompetitieTeam
                 .objects
                 .filter(deelcompetitie=deelcomp)
                 .select_related('klasse',
                                 'klasse__team')
                 .order_by('klasse__team__volgorde'))

        for team in teams:
            try:
                poule = team_pk2poule[team.pk]
            except KeyError:
                pass
            else:
                team.poule = poule
        # for

        context['teams'] = teams

        if not readonly:
            context['url_nieuwe_poule'] = reverse('CompRegio:regio-poules',
                                                  kwargs={'deelcomp_pk': deelcomp.pk})

        context['wiki_rcl_poules_url'] = reverse_handleiding(self.request, settings.HANDLEIDING_POULES)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ maak een nieuwe poule aan """
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])    # afkappen voor veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio',
                                        'nhb_regio__rayon')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'D':
            raise Http404('Poules kunnen niet meer aangepast worden')

        aantal = (RegiocompetitieTeamPoule
                  .objects
                  .filter(deelcompetitie=deelcomp)
                  .count())
        nummer = aantal + 1

        # maak een nieuwe poule aan
        RegiocompetitieTeamPoule(
                deelcompetitie=deelcomp,
                beschrijving='poule %s' % nummer).save()

        url = reverse('CompRegio:regio-poules',
                      kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class WijzigPouleView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL een poule beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_RCL_WIJZIG_POULE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            poule_pk = int(kwargs['poule_pk'][:6])      # afkappen voor de veiligheid
            poule = (RegiocompetitieTeamPoule
                     .objects
                     .select_related('deelcompetitie',
                                     'deelcompetitie__nhb_regio',
                                     'deelcompetitie__competitie')
                     .prefetch_related('teams')
                     .get(pk=poule_pk))
        except (ValueError, RegiocompetitieTeamPoule.DoesNotExist):
            raise Http404('Poule bestaat niet')

        deelcomp = poule.deelcompetitie
        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if comp.fase > 'E':
            raise Http404('Poules kunnen niet meer aangepast worden')

        context['mag_koppelen'] = (comp.fase <= 'D')

        team_pks = list(poule.teams.values_list('pk', flat=True))

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('klasse__team',
                                 'team_type')
                 .prefetch_related('regiocompetitieteampoule_set')
                 .filter(deelcompetitie=deelcomp)
                 .order_by('klasse__team__volgorde'))
        for team in teams:
            team.sel_str = 'team_%s' % team.pk
            if team.pk in team_pks:
                team.geselecteerd = True
            else:
                if team.regiocompetitieteampoule_set.count():
                    team.in_andere_poule = True

            if team.klasse:
                team.klasse_str = team.klasse.team.beschrijving
            else:
                team.klasse_str = ''        # blokkeert selectie voor poule
        # for
        context['teams'] = teams

        context['poule'] = poule
        context['url_opslaan'] = reverse('CompRegio:wijzig-poule',
                                         kwargs={'poule_pk': poule.pk})
        context['url_terug'] = reverse('CompRegio:regio-poules',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als ... knop ... """

        try:
            poule_pk = int(kwargs['poule_pk'][:6])      # afkappen voor de veiligheid
            poule = (RegiocompetitieTeamPoule
                     .objects
                     .select_related('deelcompetitie')
                     .prefetch_related('teams')
                     .get(pk=poule_pk))
        except (ValueError, RegiocompetitieTeamPoule.DoesNotExist):
            raise Http404('Poule bestaat niet')

        deelcomp = poule.deelcompetitie
        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'E':
            raise Http404('Poules kunnen niet meer aangepast worden')

        mag_koppelen = comp.fase <= 'D'

        if request.POST.get('verwijder_poule', ''):
            if mag_koppelen:
                # deze poule is niet meer nodig
                poule.delete()
        else:
            beschrijving = request.POST.get('beschrijving', '')[:100]   # afkappen voor de veiligheid
            beschrijving = beschrijving.strip()
            if poule.beschrijving != beschrijving:
                poule.beschrijving = beschrijving
                poule.save(update_fields=['beschrijving'])

            if mag_koppelen:
                gekozen = list()
                type_counts = dict()
                for team in (RegiocompetitieTeam
                             .objects
                             .prefetch_related('regiocompetitieteampoule_set')
                             .filter(deelcompetitie=deelcomp)):

                    sel_str = 'team_%s' % team.pk
                    if request.POST.get(sel_str, ''):
                        kies = False

                        if team.regiocompetitieteampoule_set.count() == 0:
                            # nog niet in te een poule, dus mag gekozen worden
                            kies = True
                        else:
                            if team.regiocompetitieteampoule_set.all()[0].pk == poule.pk:
                                # herverkozen in dezelfde poule
                                kies = True

                        if kies:
                            gekozen.append(team)

                            try:
                                type_counts[team.team_type] += 1
                            except KeyError:
                                type_counts[team.team_type] = 1
                # for

                # kijk welk team type dit gaat worden
                if len(gekozen) == 0:
                    poule.teams.clear()
                else:
                    tups = [(count, team_type.pk, team_type) for team_type, count in type_counts.items()]
                    tups.sort(reverse=True)     # hoogste eerst
                    # TODO: wat als er 2 even hoog zijn?
                    team_type = tups[0][2]

                    # laat teams toe die binnen dit team type passen
                    goede_teams = [team for team in gekozen if team.team_type == team_type]
                    goede_teams = goede_teams[:8]       # maximaal 8 teams in een poule

                    # vervang door de overgebleven teams
                    poule.teams.set(goede_teams)

        url = reverse('CompRegio:regio-poules',
                      kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# end of file
