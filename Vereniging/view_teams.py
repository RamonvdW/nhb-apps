# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.models import (CompetitieKlasse, AG_NUL,
                               DeelCompetitie, LAAG_REGIO,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Score.models import ScoreHist, aanvangsgemiddelde_opslaan

TEMPLATE_TEAMS_REGIO = 'vereniging/teams-regio.dtl'
TEMPLATE_TEAMS_REGIO_WIJZIG = 'vereniging/teams-regio-wijzig.dtl'
TEMPLATE_TEAMS_WIJZIG_AG = 'vereniging/wijzig-ag.dtl'
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

        if deelcomp.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(deelcompetitie=deelcomp,
                         vereniging=self.functie_nu.nhb_ver)
                 .order_by('volg_nr'))
        for obj in teams:
            obj.aantal = obj.gekoppelde_schutters.count()
            obj.ag_str = "%05.1f" % (obj.aanvangsgemiddelde * aantal_pijlen)

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

        if team.pk > 0:
            context['url_verwijderen'] = context['url_opslaan']

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        # for k, v in request.POST.items():
        #     print('%s=%s' % (k, v))

        deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])
        ver = self.functie_nu.nhb_ver

        try:
            team_pk = int(kwargs['team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
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

            verwijderen = False
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

            verwijderen = request.POST.get('verwijderen', None) is not None

            if not verwijderen:
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

        url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class WijzigAanvangsgemiddeldeView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_WIJZIG_AG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _mag_wijzigen_of_404(self, deelnemer):
        ver = deelnemer.bij_vereniging
        if self.rol_nu == Rollen.ROL_HWL:
            # HWL
            if ver != self.functie_nu.nhb_ver:
                raise Resolver404()
        else:
            # RCL
            if ver.regio != self.functie_nu.nhb_regio:
                raise Resolver404()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # haal de deelnemer op
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('schutterboog',
                                         'schutterboog__nhblid',
                                         'schutterboog__boogtype',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Resolver404()

        context['deelnemer'] = deelnemer

        # controleer dat deze deelnemer bekeken en gewijzigd mag worden
        self._mag_wijzigen_of_404(deelnemer)

        if deelnemer.aanvangsgemiddelde == AG_NUL:
            if not deelnemer.is_handmatig_ag:
                deelnemer.is_handmatig_ag = True
                deelnemer.save()

        deelnemer.ag_str = '%.3f' % deelnemer.aanvangsgemiddelde

        deelnemer.naam_str = deelnemer.schutterboog.nhblid.volledige_naam()
        deelnemer.boog_str = deelnemer.schutterboog.boogtype.beschrijving

        ag_hist = (ScoreHist
                   .objects
                   .filter(score__schutterboog=deelnemer.schutterboog,
                           score__is_ag=True)
                   .order_by('-when'))
        for obj in ag_hist:
            obj.mutatie_str = "%.3f --> %.3f" % (obj.oude_waarde / 1000, obj.nieuwe_waarde / 1000)
        # for
        context['ag_hist'] = ag_hist

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' wordt gebruikt """

        # haal de deelnemer op
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('deelcompetitie',
                                         'deelcompetitie__competitie',
                                         'schutterboog',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Resolver404()

        # controleer dat deze deelnemer bekeken en gewijzigd mag worden
        self._mag_wijzigen_of_404(deelnemer)

        nieuw_ag = request.POST.get('nieuw_ag', '')
        if nieuw_ag:
            try:
                nieuw_ag = float(nieuw_ag)
            except ValueError:
                raise Resolver404()

            # controleer dat het een redelijk AG is
            if nieuw_ag < 1.0 or nieuw_ag >= 10.0:
                raise Resolver404()

            aanvangsgemiddelde_opslaan(
                    deelnemer.schutterboog,
                    deelnemer.deelcompetitie.competitie.afstand,
                    nieuw_ag,
                    request.user,
                    "Nieuw handmatig AG ingevoerd door beheerder")

            deelnemer.aanvangsgemiddelde = nieuw_ag
            deelnemer.save()

        if self.rol_nu == Rollen.ROL_HWL:
            url = reverse('Vereniging:teams-regio',
                          kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})
        else:
            url = reverse('Competitie:regio-ag-controle',
                          kwargs={'comp_pk': deelnemer.deelcompetitie.competitie.pk,
                                  'regio_nr': deelnemer.deelcompetitie.nhb_regio.regio_nr})

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

        if team.deelcompetitie.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        team.ag_str = "%5.1f" % (team.aanvangsgemiddelde * aantal_pijlen)

        pks = team.gekoppelde_schutters.values_list('pk', flat=True)

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

        team.gekoppelde_schutters.clear()
        team.gekoppelde_schutters.add(*pks)

        ags = team.gekoppelde_schutters.values_list('aanvangsgemiddelde', flat=True)
        ags = list(ags)

        if len(ags) >= 3:
            # neem de beste 3 schutters
            ags.sort(reverse=True)
            ags = ags[:3]

            # bereken het gemiddelde
            ag = sum(ags)

            # bepaal de wedstrijdklasse
            team.klasse = None
            comp = team.deelcompetitie.competitie
            for klasse in (CompetitieKlasse
                           .objects
                           .filter(competitie=comp,
                                   team__team_type=team.team_type)
                           .order_by('min_ag')):        # oplopend
                if ag >= klasse.min_ag:
                    team.klasse = klasse
            # for
        else:
            ag = AG_NUL
            team.klasse = None

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

        # rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        # ver = functie_nu.nhb_ver

        menu_dynamics(self.request, context, actief='vereniging')
        return context

# end of file
