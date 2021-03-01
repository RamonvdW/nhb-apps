# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.models import DeelCompetitie, LAAG_REGIO, RegioCompetitieSchutterBoog, RegiocompetitieTeam, AG_NUL
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie

TEMPLATE_TEAMS_REGIO = 'vereniging/teams-regio.dtl'
TEMPLATE_TEAMS_REGIO_WIJZIG = 'vereniging/teams-regio-wijzig.dtl'
TEMPLATE_TEAMS_KOPPELEN = 'vereniging/teams-koppelen.dtl'
TEMPLATE_TEAMS_RK = 'vereniging/teams-rk.dtl'


class TeamsRegioView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de regiocompetitie.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_REGIO

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _get_deelcomp(self, deelcomp_pk) -> DeelCompetitie:

        # haal de gevraagde deelcompetitie op
        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             laag=LAAG_REGIO,                           # moet regiocompetitie zijn
                             nhb_regio=self.functie_nu.nhb_ver.regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'C':
            # staat niet meer open voor instellen regiocompetitie teams
            raise Resolver404()

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        context['vaste_teams'] = deelcomp.regio_heeft_vaste_teams

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(deelcompetitie=deelcomp,
                         vereniging=self.functie_nu.nhb_ver)
                 .order_by('volg_nr'))
        for obj in teams:
            if deelcomp.regio_heeft_vaste_teams:
                obj.aantal = obj.vaste_schutters.count()

            obj.url_wijzig = reverse('Vereniging:teams-regio-wijzig',
                                     kwargs={'deelcomp_pk': deelcomp.pk,
                                             'team_pk': obj.pk})

            obj.url_koppelen = reverse('Vereniging:teams-regio-koppelen',
                                       kwargs={'team_pk': obj.pk})
        # for
        context['teams'] = teams

        context['url_nieuw_team'] = reverse('Vereniging:teams-regio-nieuw',
                                            kwargs={'deelcomp_pk': deelcomp.pk})

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('schutterboog',
                                      'schutterboog__nhblid',
                                      'schutterboog__boogtype')
                      .prefetch_related('regiocompetitieteam_set')
                      .filter(deelcompetitie=deelcomp,
                              bij_vereniging=self.functie_nu.nhb_ver,
                              inschrijf_voorkeur_team=True)
                      .order_by('schutterboog__boogtype__volgorde',
                                '-aanvangsgemiddelde'))
        for obj in deelnemers:
            obj.boog_str = obj.schutterboog.boogtype.beschrijving
            obj.naam_str = "[%s] %s" % (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.nhblid.volledige_naam())
            obj.ag_str = "%.3f" % obj.aanvangsgemiddelde
            try:
                team = obj.regiocompetitieteam_set.all()[0]
            except IndexError:
                pass
            else:
                obj.in_team_str = team.maak_team_naam_kort()
            if obj.aanvangsgemiddelde == AG_NUL:
                obj.is_handmatig_ag = True
                obj.rood_ag = True
            if obj.is_handmatig_ag:
                obj.ag_str += " (handmatig)"
                obj.url_wijzig_ag = reverse('Vereniging:wijzig-ag',
                                            kwargs={'deelnemer_pk': obj.pk})
        # for
        context['deelnemers'] = deelnemers

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class WijzigRegioTeamsView(UserPassesTestMixin, TemplateView):

    """ laat de HWL een nieuw team aanmaken of een bestaand team wijzigen
        voor de regiocompetitie
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_REGIO_WIJZIG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _get_deelcomp(self, deelcomp_pk) -> DeelCompetitie:

        # haal de gevraagde deelcompetitie op
        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             laag=LAAG_REGIO,                           # moet regiocompetitie zijn
                             regio_organiseert_teamcompetitie=True,
                             nhb_regio=self.functie_nu.nhb_ver.regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'C':
            # staat niet meer open voor instellen regiocompetitie teams
            raise Resolver404()

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

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
            team = RegiocompetitieTeam.objects.get(pk=team_pk, deelcompetitie=deelcomp)
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Resolver404()
        except KeyError:
            # dit is een nieuw team
            team = RegiocompetitieTeam(
                            pk=0,
                            vereniging=self.functie_nu.nhb_ver,
                            team_type=teamtype_default)

        context['team'] = team

        for obj in teams:
            obj.actief = team.team_type == obj
        # for

        context['url_opslaan'] = reverse('Vereniging:teams-regio-wijzig',
                                         kwargs={'deelcomp_pk': deelcomp.pk,
                                                 'team_pk': team.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        # for k, v in request.POST.items():
        #     print('%s=%s' % (k, v))

        deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])
        ver = self.functie_nu.nhb_ver

        try:
            team_pk = int(kwargs['team_pk'][:6])    # afkappen voor de veiligheid
        except ValueError:
            raise Resolver404()

        if team_pk == 0:
            # nieuw team

            volg_nrs = (RegiocompetitieTeam
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                vereniging=ver)
                        .values_list('volg_nr', flat=True))
            volg_nrs = list(volg_nrs)
            volg_nrs.append(0)
            next_nr = max(volg_nrs) + 1

            if len(volg_nrs) > 10:
                # te veel teams
                raise Resolver404()

            afkorting = request.POST.get('team_type', '')
            try:
                team_type = TeamType.objects.get(afkorting=afkorting)
            except TeamType.DoesNotExist:
                raise Resolver404()

            team = RegiocompetitieTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=team_type,
                            team_naam=' ')
            team.save()
        else:
            try:
                team = (RegiocompetitieTeam
                        .objects
                        .select_related('team_type')
                        .get(pk=team_pk,
                             deelcompetitie=deelcomp,
                             vereniging=ver))
            except RegiocompetitieTeam.DoesNotExist:
                raise Resolver404()

            afkorting = request.POST.get('team_type', '')
            if team.team_type.afkorting != afkorting:
                try:
                    team_type = TeamType.objects.get(afkorting=afkorting)
                except TeamType.DoesNotExist:
                    raise Resolver404()

                team.team_type = team_type
                team.save()

                # verwijder eventueel gekoppelde sporters bij wijziging team type,
                # om verkeerde boog typen te voorkomen
                team.vaste_schutters.clear()

        team_naam = request.POST.get('team_naam', '')
        team_naam = team_naam.strip()
        if team.team_naam != team_naam:
            if team_naam == '':
                team_naam = "%s-%s" % (ver.nhb_nr, team.volg_nr)

            team.team_naam = team_naam
            team.save()

        url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class TeamsRegioKoppelLedenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL leden van zijn vereniging koppelen aan een team """

    template_name = TEMPLATE_TEAMS_KOPPELEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            team_pk = int(kwargs['team_pk'][:6])
            team = (RegiocompetitieTeam
                    .objects
                    .select_related('deelcompetitie',
                                    'team_type')
                    .prefetch_related('team_type__boog_typen')
                    .get(pk=team_pk,
                         vereniging=self.functie_nu.nhb_ver))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Resolver404()

        context['team'] = team

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        pks = team.vaste_schutters.values_list('pk', flat=True)

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=team.deelcompetitie,
                              inschrijf_voorkeur_team=True,
                              bij_vereniging=self.functie_nu.nhb_ver,
                              schutterboog__boogtype__in=boog_pks)
                      .order_by('-aanvangsgemiddelde'))
        for obj in deelnemers:
            obj.sel_str = "deelnemer_%s" % obj.pk
            obj.naam_str = obj.schutterboog.nhblid.volledige_naam()
            obj.boog_str = obj.schutterboog.boogtype.beschrijving
            obj.blokkeer = (obj.aanvangsgemiddelde == AG_NUL)
            obj.ag_str = "%.3f" % obj.aanvangsgemiddelde
            obj.geselecteerd = (obj.pk in pks)
            if not obj.geselecteerd:
                if obj.regiocompetitieteam_set.count() > 0:
                    obj.blokkeer = True
        # for
        context['deelnemers'] = deelnemers

        context['url_opslaan'] = reverse('Vereniging:teams-regio-koppelen',
                                         kwargs={'team_pk': team.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            team_pk = int(kwargs['team_pk'][:6])
            team = (RegiocompetitieTeam
                    .objects
                    .select_related('deelcompetitie',
                                    'team_type')
                    .prefetch_related('team_type__boog_typen')
                    .get(pk=team_pk,
                         vereniging=self.functie_nu.nhb_ver))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Resolver404()

        if team.deelcompetitie.regio_heeft_vaste_teams:
            pks = list()
            for key in request.POST.keys():
                if key.startswith('deelnemer_'):
                    try:
                        pk = int(key[10:])
                    except ValueError:
                        pass
                    else:
                        pks.append(pk)
            # for

            team.vaste_schutters.clear()
            team.vaste_schutters.add(*pks)

            ags = team.vaste_schutters.values_list('aanvangsgemiddelde', flat=True)
            ags = list(ags)

            if len(ags) >= 3:
                # neem de beste 3 schutters
                ags.sort(reverse=True)
                ags = ags[:3]

                # bereken het gemiddelde
                ag = sum(ags) / len(ags)
            else:
                ag = AG_NUL

            team.aanvangsgemiddelde = ag
            team.save()

        url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': team.deelcompetitie.pk})
        return HttpResponseRedirect(url)


class TeamsRkView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de rayonkampioenschappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_RK

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        ver = functie_nu.nhb_ver

        menu_dynamics(self.request, context, actief='vereniging')
        return context

# end of file
