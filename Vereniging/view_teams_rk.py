# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.models import (CompetitieKlasse, AG_NUL, DeelCompetitie, LAAG_RK,
                               RegioCompetitieSchutterBoog, KampioenschapTeam)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Score.models import ScoreHist, SCORE_TYPE_TEAM_AG
from Score.operations import score_teams_ag_opslaan
import datetime


TEMPLATE_TEAMS_RK = 'vereniging/teams-rk.dtl'
TEMPLATE_TEAMS_RK_WIJZIG = 'vereniging/teams-rk-wijzig.dtl'


class TeamsRkView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de rayonkampioenschappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_RK
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def _get_deelcomp_rk(self, deelcomp_rk_pk):
        # haal de gevraagde deelcompetitie op
        try:
            deelcomp_pk = int(deelcomp_rk_pk[:6])  # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             laag=LAAG_RK,      # moet RK zijn
                             nhb_rayon=self.functie_nu.nhb_ver.regio.rayon))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404()

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if not ('E' <= comp.fase <= 'K'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase 1')

        vanaf = comp.eerste_wedstrijd + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase 2')

        return deelcomp

    def _get_teams(self, deelcomp_rk):

        if deelcomp_rk.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        teams = (KampioenschapTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(deelcompetitie=deelcomp_rk,
                         vereniging=self.functie_nu.nhb_ver)
                 .annotate(gekoppelde_schutters_count=Count('schutters'))
                 .order_by('volg_nr'))
        for obj in teams:
            obj.aantal = obj.gekoppelde_schutters_count
            obj.ag_str = "%05.1f" % (obj.aanvangsgemiddelde * aantal_pijlen)
            obj.ag_str = obj.ag_str.replace('.', ',')

            obj.url_wijzig = reverse('Vereniging:teams-rk-wijzig',
                                     kwargs={'deelcomp_pk': deelcomp_rk.pk,
                                             'team_pk': obj.pk})

            # koppelen == bekijken
            obj.url_koppelen = reverse('Vereniging:teams-regio-koppelen',
                                       kwargs={'team_pk': obj.pk})
        # for

        return teams

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.nhb_ver

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp_rk = self._get_deelcomp_rk(kwargs['deelcomp_pk'])

        context['teams'] = self._get_teams(deelcomp_rk)

        context['url_nieuw_team'] = reverse('Vereniging:teams-rk-nieuw',
                                            kwargs={'deelcomp_pk': deelcomp_rk.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class WijzigRKTeamsView(UserPassesTestMixin, TemplateView):

    """ laat de HWL een nieuw team aanmaken of een bestaand team wijzigen voor het RK
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_RK_WIJZIG
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def _get_deelcomp_rk(self, deelcomp_rk_pk) -> DeelCompetitie:
        # haal de gevraagde deelcompetitie op
        try:
            deelcomp_pk = int(deelcomp_rk_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             laag=LAAG_RK,                           # moet RK zijn
                             nhb_rayon=self.functie_nu.nhb_ver.regio.rayon))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if not ('E' <= comp.fase <= 'K'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase')

        vanaf = comp.eerste_wedstrijd + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase')

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp_rk(kwargs['deelcomp_pk'])
        ver = self.functie_nu.nhb_ver

        teamtype_default = None
        teams = TeamType.objects.order_by('volgorde')
        for obj in teams:
            obj.choice_name = obj.afkorting
            if obj.afkorting == 'R':
                teamtype_default = obj
        # for
        context['opt_team_type'] = teams

        try:
            team_pk = int(kwargs['team_pk'][:6])
            team = (KampioenschapTeam
                    .objects
                    .get(pk=team_pk,
                         deelcompetitie=deelcomp,
                         vereniging=ver))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')
        except KeyError:
            # dit is een nieuw team
            team = KampioenschapTeam(
                            pk=0,
                            vereniging=self.functie_nu.nhb_ver,
                            team_type=teamtype_default)

        context['team'] = team

        for obj in teams:
            obj.actief = team.team_type == obj
        # for

        context['url_opslaan'] = reverse('Vereniging:teams-rk-wijzig',
                                         kwargs={'deelcomp_pk': deelcomp.pk,
                                                 'team_pk': team.pk})

        if team.pk > 0:
            context['url_verwijderen'] = context['url_opslaan']

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        deelcomp = self._get_deelcomp_rk(kwargs['deelcomp_pk'])

        ver = self.functie_nu.nhb_ver

        try:
            team_pk = int(kwargs['team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
            raise Http404('Slechte parameter')

        if team_pk == 0:
            # nieuw team
            volg_nrs = (KampioenschapTeam
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                vereniging=ver)
                        .values_list('volg_nr', flat=True))
            volg_nrs = list(volg_nrs)
            volg_nrs.append(0)
            next_nr = max(volg_nrs) + 1

            # TODO: elke vereniging maximaal 2 teams per klasse?
            if len(volg_nrs) > 10:
                # te veel teams
                raise Http404('Maximum van 10 teams is bereikt')

            afkorting = request.POST.get('team_type', '')
            try:
                team_type = TeamType.objects.get(afkorting=afkorting)
            except TeamType.DoesNotExist:
                raise Http404()

            team = KampioenschapTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=team_type,
                            team_naam=' ')
            team.save()

            verwijderen = False
        else:
            try:
                team = (KampioenschapTeam
                        .objects
                        .select_related('team_type')
                        .get(pk=team_pk,
                             deelcompetitie=deelcomp))
            except KampioenschapTeam.DoesNotExist:
                raise Http404()

            if self.rol_nu == Rollen.ROL_HWL:
                if team.vereniging != self.functie_nu.nhb_ver:
                    raise Http404('Team is niet van jouw vereniging')

            verwijderen = request.POST.get('verwijderen', None) is not None

            if not verwijderen:
                afkorting = request.POST.get('team_type', '')
                if team.team_type.afkorting != afkorting:
                    try:
                        team_type = TeamType.objects.get(afkorting=afkorting)
                    except TeamType.DoesNotExist:
                        raise Http404()

                    team.team_type = team_type
                    team.aanvangsgemiddelde = 0.0
                    team.klasse = None
                    team.save()

                    # verwijder eventueel gekoppelde sporters bij wijziging team type,
                    # om verkeerde boog typen te voorkomen
                    team.gekoppelde_schutters.clear()

        if not verwijderen:
            team_naam = request.POST.get('team_naam', '')
            team_naam = team_naam.strip()
            if team.team_naam != team_naam:
                if team_naam == '':
                    team_naam = "%s-%s" % (ver.ver_nr, team.volg_nr)

                team.team_naam = team_naam
                team.save()
        else:
            team.delete()

        url = reverse('Vereniging:teams-rk', kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


# end of file
