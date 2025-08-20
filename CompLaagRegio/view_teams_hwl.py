# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.models import TeamType
from Competitie.models import (CompetitieTeamKlasse, Regiocompetitie, RegiocompetitieSporterBoog,
                               RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               update_uitslag_teamcompetitie)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Score.definities import AG_NUL, AG_DOEL_TEAM
from Score.models import AanvangsgemiddeldeHist
from Score.operations import score_teams_ag_opslaan
import datetime


TEMPLATE_TEAMS_REGIO = 'complaagregio/hwl-teams.dtl'
TEMPLATE_TEAMS_REGIO_WIJZIG = 'complaagregio/hwl-teams-wijzig.dtl'
TEMPLATE_TEAMS_WIJZIG_AG = 'complaagregio/wijzig-team-ag.dtl'
TEMPLATE_TEAMS_KOPPELEN = 'complaagregio/hwl-teams-koppelen.dtl'
TEMPLATE_TEAMS_INVALLERS = 'complaagregio/hwl-teams-invallers.dtl'
TEMPLATE_TEAMS_INVALLERS_KOPPELEN = 'complaagregio/hwl-teams-invallers-koppelen.dtl'


def bepaal_team_sterkte_en_klasse(team):
    """ gebruik AG van gekoppelde sporters om team aanvangsgemiddelde te berekenen
        en bepaal aan de hand daarvan de team-wedstrijdklasse
    """
    ags = team.leden.values_list('ag_voor_team', flat=True)
    ags = list(ags)

    team.team_klasse = None

    if len(ags) >= 3:
        # bereken de team sterkte: de som van de 3 sterkste sporters
        ags.sort(reverse=True)
        ag = sum(ags[:3])

        # bepaal de wedstrijdklasse
        comp = team.regiocompetitie.competitie
        for klasse in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               team_type=team.team_type,
                               is_voor_teams_rk_bk=False)
                       .order_by('min_ag',
                                 '-volgorde')):  # oplopend AG (=hogere klasse later)

            if ag >= klasse.min_ag:
                team.team_klasse = klasse
        # for
    else:
        ag = AG_NUL

    team.aanvangsgemiddelde = ag
    team.save(update_fields=['team_klasse', 'aanvangsgemiddelde'])


class TeamsRegioView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de regiocompetitie.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_REGIO
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def _get_deelcomp(self, deelcomp_pk) -> Regiocompetitie:

        # haal de gevraagde regiocompetitie op
        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie', 'regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             regio=self.functie_nu.vereniging.regio))
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if comp.fase_teams > 'F':
            # staat niet meer open voor instellen regiocompetitie teams
            raise Http404('Competitie is niet in de juiste fase')

        self.readonly = comp.fase_teams > 'C'

        if self.rol_nu == Rol.ROL_WL:
            self.readonly = True

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        context['readonly'] = self.readonly

        now = timezone.now()
        einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                  month=deelcomp.begin_fase_D.month,
                                  day=deelcomp.begin_fase_D.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        einde = timezone.make_aware(einde)
        mag_wijzigen = (now < einde) and not self.readonly
        context['mag_wijzigen'] = mag_wijzigen

        if deelcomp.competitie.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(regiocompetitie=deelcomp,
                         vereniging=self.functie_nu.vereniging)
                 .annotate(leden_count=Count('leden'))
                 .order_by('volg_nr'))

        for obj in teams:
            obj.aantal = obj.leden_count
            ag_str = "%05.1f" % (obj.aanvangsgemiddelde * aantal_pijlen)
            obj.ag_str = ag_str.replace('.', ',')

            if mag_wijzigen:
                obj.url_wijzig = reverse('CompLaagRegio:teams-regio-wijzig',
                                         kwargs={'deelcomp_pk': deelcomp.pk,
                                                 'team_pk': obj.pk})

            # koppelen == bekijken
            obj.url_koppelen = reverse('CompLaagRegio:teams-regio-koppelen',
                                       kwargs={'team_pk': obj.pk})
        # for
        context['teams'] = teams

        if mag_wijzigen:
            context['url_nieuw_team'] = reverse('CompLaagRegio:teams-regio',
                                                kwargs={'deelcomp_pk': deelcomp.pk})

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'sporterboog__boogtype')
                      .prefetch_related('regiocompetitieteam_set')
                      .filter(regiocompetitie=deelcomp,
                              bij_vereniging=self.functie_nu.vereniging,
                              inschrijf_voorkeur_team=True)
                      .order_by('sporterboog__boogtype__volgorde',
                                '-ag_voor_team'))
        for obj in deelnemers:
            obj.boog_str = obj.sporterboog.boogtype.beschrijving
            obj.naam_str = "[%s] %s" % (obj.sporterboog.sporter.lid_nr, obj.sporterboog.sporter.volledige_naam())
            ag_str = "%.3f" % obj.ag_voor_team
            obj.ag_str = ag_str.replace('.', ',')

            try:
                team = obj.regiocompetitieteam_set.all()[0]
            except IndexError:
                obj.in_team_str = '??'
            else:
                obj.in_team_str = team.maak_team_naam_kort()

            if obj.ag_voor_team < 0.001:
                obj.rood_ag = True

            if obj.ag_voor_team_mag_aangepast_worden:
                obj.ag_str += " (handmatig)"
                if mag_wijzigen:
                    obj.url_wijzig_ag = reverse('CompLaagRegio:wijzig-ag',
                                                kwargs={'deelnemer_pk': obj.pk})
        # for
        context['deelnemers'] = deelnemers

        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % deelcomp.competitie.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer vereniging'),
            (url_overzicht + anker, deelcomp.competitie.beschrijving.replace(' competitie', '')),
            (None, 'Teams Regio')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ maak een nieuw team aan """
        _ = self._get_deelcomp(kwargs['deelcomp_pk'])

        if self.rol_nu != Rol.ROL_HWL:
            raise PermissionDenied('Geen toegang met deze rol')

        ver = self.functie_nu.vereniging

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        now = timezone.now()
        einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                  month=deelcomp.begin_fase_D.month,
                                  day=deelcomp.begin_fase_D.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        einde = timezone.make_aware(einde)
        if not (now < einde):
            raise Http404('De deadline is gepasseerd')

        # nieuw team aanmaken
        volg_nrs = (RegiocompetitieTeam
                    .objects
                    .filter(regiocompetitie=deelcomp,
                            vereniging=ver)
                    .values_list('volg_nr', flat=True))
        volg_nrs = list(volg_nrs)
        volg_nrs.append(0)
        next_nr = max(volg_nrs) + 1

        if len(volg_nrs) > 25:      # 10 is te weinig voor grote verenigingen
            # te veel teams
            raise Http404('Maximum van 25 teams is bereikt')

        # afkorting is optioneel, voornamelijk bedoeld voor de autotester
        afkorting = request.POST.get('team_type', 'R2')
        afkorting = afkorting[:6]       # afkappen voor de veiligheid
        try:
            team_type = TeamType.objects.get(afkorting=afkorting)
        except TeamType.DoesNotExist:
            raise Http404('Verkeerd team type')

        naam_str = "%s-%s" % (ver.ver_nr, next_nr)

        RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=ver,
                    volg_nr=next_nr,
                    team_type=team_type,
                    team_naam=naam_str).save()

        # terug naar de pagina met teams
        url = reverse('CompLaagRegio:teams-regio',
                      kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


class WijzigRegioTeamsView(UserPassesTestMixin, TemplateView):

    """ laat de HWL een nieuw team aanmaken of een bestaand team wijzigen (of zelfs verwijderen)
        voor de regiocompetitie
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_REGIO_WIJZIG
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL)

    def _get_deelcomp(self, deelcomp_pk) -> Regiocompetitie:
        # haal de gevraagde regiocompetitie op

        if self.rol_nu == Rol.ROL_HWL:
            regio = self.functie_nu.vereniging.regio
        else:
            # RCL
            regio = self.functie_nu.regio

        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie', 'regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             regio_organiseert_teamcompetitie=True,
                             regio=regio))
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if comp.fase_teams > 'D':
            # mag niet meer wijzigen
            raise Http404('Competitie is niet in de juiste fase')

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu == Rol.ROL_RCL:
            raise Http404('Verkeerde rol')

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])
        ver = self.functie_nu.vereniging

        now = timezone.now()
        einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                  month=deelcomp.begin_fase_D.month,
                                  day=deelcomp.begin_fase_D.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        einde = timezone.make_aware(einde)
        mag_wijzigen = (now <= einde)

        try:
            team_pk = int(kwargs['team_pk'][:6])        # afkappen voor de veiligheid
            team = (RegiocompetitieTeam
                    .objects
                    .get(pk=team_pk,
                         regiocompetitie=deelcomp,
                         vereniging=ver))
        except (KeyError, ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')

        context['team'] = team

        context['opt_team_type'] = teamtypes = (deelcomp.competitie.teamtypen.order_by('volgorde'))
        for obj in teamtypes:
            obj.choice_name = obj.afkorting
            obj.actief = (team.team_type == obj)
        # for

        if mag_wijzigen:
            context['url_opslaan'] = reverse('CompLaagRegio:teams-regio-wijzig',
                                             kwargs={'deelcomp_pk': deelcomp.pk,
                                                     'team_pk': team.pk})

            context['url_verwijderen'] = context['url_opslaan']
        else:
            context['readonly'] = True

        comp = deelcomp.competitie
        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk}),
                    'Teams Regio %s' % comp.beschrijving.replace(' competitie', '')),
                (None, 'Wijzig team')
            )
        else:
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('CompBeheer:overzicht',
                         kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
                (None, 'Teams'),    # TODO: details invullen
                (None, 'Wijzig team')
            )

        return context

    def post(self, request, *args, **kwargs):
        deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        try:
            team_pk = int(kwargs['team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
            raise Http404('Geen valide parameter')

        try:
            team = (RegiocompetitieTeam
                    .objects
                    .select_related('team_type')
                    .get(pk=team_pk,
                         regiocompetitie=deelcomp))
        except RegiocompetitieTeam.DoesNotExist:
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            ver = self.functie_nu.vereniging

            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                      month=deelcomp.begin_fase_D.month,
                                      day=deelcomp.begin_fase_D.day,
                                      hour=0,
                                      minute=0,
                                      second=0)
            einde = timezone.make_aware(einde)
            mag_wijzigen = (now <= einde)
            if not mag_wijzigen:
                raise Http404('Mag niet (meer) wijzigen')
        else:
            # RCL
            ver = None      # wordt later ingevuld

        if self.rol_nu == Rol.ROL_HWL:
            if team.vereniging != self.functie_nu.vereniging:
                raise Http404('Team is niet van jouw vereniging')

        verwijderen = request.POST.get('verwijderen', None) is not None

        if not verwijderen:
            afkorting = request.POST.get('team_type', '')
            afkorting = afkorting[:6]       # afkappen voor de veiligheid
            if team.team_type.afkorting != afkorting:
                try:
                    team_type = TeamType.objects.get(afkorting=afkorting)
                except TeamType.DoesNotExist:
                    raise Http404('Verkeerde parameter')

                team.team_type = team_type
                team.aanvangsgemiddelde = 0.0
                team.team_klasse = None
                team.save()

                # verwijder eventueel gekoppelde sporters bij wijziging team type,
                # om verkeerde boog typen te voorkomen
                team.leden.clear()

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

        if self.rol_nu == Rol.ROL_HWL:
            url = reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        else:
            url = reverse('CompLaagRegio:regio-teams', kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


class WijzigTeamAGView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_WIJZIG_AG
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL)

    def _mag_wijzigen_of_404(self, deelnemer):
        ver = deelnemer.bij_vereniging
        if self.rol_nu == Rol.ROL_HWL:
            # HWL
            if ver != self.functie_nu.vereniging:
                raise PermissionDenied('Niet lid van jouw vereniging')
        else:
            # RCL
            if ver.regio != self.functie_nu.regio:
                raise PermissionDenied('Niet lid van een vereniging in jouw regio')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # haal de deelnemer op
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('sporterboog',
                                         'sporterboog__sporter',
                                         'sporterboog__boogtype',
                                         'bij_vereniging',
                                         'regiocompetitie__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        context['deelnemer'] = deelnemer

        # controleer dat deze deelnemer bekeken en gewijzigd mag worden
        self._mag_wijzigen_of_404(deelnemer)

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        deelnemer.boog_str = deelnemer.sporterboog.boogtype.beschrijving

        ag_str = '%.3f' % deelnemer.ag_voor_team
        deelnemer.ag_str = ag_str.replace('.', ',')

        ag_hist = (AanvangsgemiddeldeHist
                   .objects
                   .filter(ag__sporterboog=deelnemer.sporterboog,
                           ag__afstand_meter=deelnemer.regiocompetitie.competitie.afstand,
                           ag__doel=AG_DOEL_TEAM)
                   .order_by('-when'))
        for obj in ag_hist:
            obj.oude_waarde_str = "%.3f" % obj.oude_waarde
            obj.nieuwe_waarde_str = "%.3f" % obj.nieuwe_waarde
        # for
        context['ag_hist'] = ag_hist

        comp = deelnemer.regiocompetitie.competitie
        comp.bepaal_fase()

        if comp.fase_teams < 'F':
            context['url_opslaan'] = reverse('CompLaagRegio:wijzig-ag',
                                             kwargs={'deelnemer_pk': deelnemer.pk})

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelnemer.regiocompetitie.pk}),
                    'Teams Regio %s' % comp.beschrijving.replace(' competitie', '')),
                (None, 'Wijzig AG')
            )
        else:
            # RCL
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                 comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRegio:regio-ag-controle',
                         kwargs={'comp_pk': comp.pk,
                                 'regio_nr': deelnemer.regiocompetitie.regio.regio_nr}),
                 'AG controle'),
                (None, 'Wijzig AG')
            )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' wordt gebruikt """

        # haal de deelnemer op
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('regiocompetitie',
                                         'regiocompetitie__competitie',
                                         'sporterboog',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        # controleer dat deze deelnemer bekeken en gewijzigd mag worden
        self._mag_wijzigen_of_404(deelnemer)

        nieuw_ag = request.POST.get('nieuw_ag', '')
        if nieuw_ag:
            try:
                nieuw_ag = float(nieuw_ag[:6])      # afkappen voor de veiligheid
            except ValueError:
                raise Http404('Geen goed AG')

            # controleer dat het een redelijk AG is
            if nieuw_ag < 1.0 or nieuw_ag >= 10.0:
                raise Http404('Geen goed AG')

            door_account = get_account(request)

            score_teams_ag_opslaan(
                    deelnemer.sporterboog,
                    deelnemer.regiocompetitie.competitie.afstand,
                    nieuw_ag,
                    door_account,
                    "Nieuw handmatig AG voor teams")

            deelnemer.ag_voor_team = nieuw_ag
            deelnemer.save()

            try:
                team = deelnemer.regiocompetitieteam_set.all()[0]
            except IndexError:
                # niet in een team
                pass
            else:
                bepaal_team_sterkte_en_klasse(team)

        if self.rol_nu == Rol.ROL_HWL:
            url = reverse('CompLaagRegio:teams-regio',
                          kwargs={'deelcomp_pk': deelnemer.regiocompetitie.pk})
        else:
            url = reverse('CompLaagRegio:regio-ag-controle',
                          kwargs={'comp_pk': deelnemer.regiocompetitie.competitie.pk,
                                  'regio_nr': deelnemer.regiocompetitie.regio.regio_nr})

        return HttpResponseRedirect(url)


class TeamsRegioKoppelLedenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL leden van zijn vereniging koppelen aan een team """

    template_name = TEMPLATE_TEAMS_KOPPELEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            team_pk = int(kwargs['team_pk'][:6])        # afkappen voor de veiligheid
            team = (RegiocompetitieTeam
                    .objects
                    .select_related('regiocompetitie',
                                    'team_type')
                    .prefetch_related('team_type__boog_typen')
                    .get(pk=team_pk))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            ver = self.functie_nu.vereniging
            if team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            # RCL
            ver = team.vereniging

        context['team'] = team

        context['deelcomp'] = deelcomp = team.regiocompetitie

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if self.rol_nu == Rol.ROL_HWL:
            context['readonly'] = readonly = (comp.fase_teams > 'D')
            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                      month=deelcomp.begin_fase_D.month,
                                      day=deelcomp.begin_fase_D.day,
                                      hour=0,
                                      minute=0,
                                      second=0)
            einde = timezone.make_aware(einde)
            mag_wijzigen = (now <= einde) and not readonly
        else:
            # RCL
            context['readonly'] = (comp.fase_teams > 'D')       # TODO: de RCL langer rechten geven?
            mag_wijzigen = True

        context['mag_wijzigen'] = mag_wijzigen

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        if deelcomp.competitie.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
        team.ag_str = ag_str.replace('.', ',')

        if mag_wijzigen:
            pks = team.leden.values_list('pk', flat=True)

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie=deelcomp,
                                  inschrijf_voorkeur_team=True,
                                  bij_vereniging=ver,
                                  sporterboog__boogtype__in=boog_pks)
                          .annotate(in_team_count=Count('regiocompetitieteam'))
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype')
                          .order_by('-ag_voor_team'))
            for obj in deelnemers:
                obj.sel_str = "deelnemer_%s" % obj.pk
                obj.naam_str = "[%s] %s" % (obj.sporterboog.sporter.lid_nr, obj.sporterboog.sporter.volledige_naam())
                obj.boog_str = obj.sporterboog.boogtype.beschrijving
                ag_str = "%.3f" % obj.ag_voor_team
                obj.ag_str = ag_str.replace('.', ',')
                obj.blokkeer = (obj.ag_voor_team < 0.001)
                obj.geselecteerd = (obj.pk in pks)          # vinkje zetten: gekoppeld aan dit team
                if not obj.geselecteerd:
                    if obj.in_team_count > 0:
                        obj.blokkeer = True                 # niet te selecteren: gekoppeld aan een ander team
            # for
            context['deelnemers'] = deelnemers

            context['url_opslaan'] = reverse('CompLaagRegio:teams-regio-koppelen',
                                             kwargs={'team_pk': team.pk})
        else:
            context['gekoppeld'] = gekoppeld = (team
                                                .leden
                                                .select_related('sporterboog',
                                                                'sporterboog__sporter',
                                                                'sporterboog__boogtype')
                                                .order_by('-ag_voor_team'))
            for obj in gekoppeld:
                obj.naam_str = "[%s] %s" % (obj.sporterboog.sporter.lid_nr, obj.sporterboog.sporter.volledige_naam())
                obj.boog_str = obj.sporterboog.boogtype.beschrijving
                ag_str = "%.3f" % obj.ag_voor_team
                obj.ag_str = ag_str.replace('.', ',')
            # for

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk}),
                'Teams Regio %s' % comp.beschrijving.replace(' competitie', '')),
            (None, 'Koppel teamleden')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            team_pk = int(kwargs['team_pk'][:6])        # afkappen voor de veiligheid
            team = (RegiocompetitieTeam
                    .objects
                    .select_related('regiocompetitie',
                                    'team_type')
                    .prefetch_related('team_type__boog_typen')
                    .get(pk=team_pk))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            ver = self.functie_nu.vereniging
            if team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = team.vereniging

        deelcomp = team.regiocompetitie

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if self.rol_nu == Rol.ROL_HWL:
            readonly = (comp.fase_teams > 'D')
            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.begin_fase_D.year,
                                      month=deelcomp.begin_fase_D.month,
                                      day=deelcomp.begin_fase_D.day,
                                      hour=0,
                                      minute=0,
                                      second=0)
            einde = timezone.make_aware(einde)
            mag_wijzigen = (now <= einde) and not readonly
        else:
            # RCL
            readonly = (comp.fase_teams > 'D')
            mag_wijzigen = not readonly

        if not mag_wijzigen:
            raise Http404('Voorbij de einddatum voor wijzigingen')

        # toegestane boogtypen en schutters
        boog_pks = team.team_type.boog_typen.values_list('pk', flat=True)
        bezet_pks = team.leden.values_list('pk', flat=True)

        # leden die nog niet in een team zitten
        ok1_pks = (RegiocompetitieSporterBoog
                   .objects
                   .exclude(pk__in=bezet_pks)
                   .filter(regiocompetitie=team.regiocompetitie,
                           inschrijf_voorkeur_team=True,
                           ag_voor_team__gte=1.0,
                           bij_vereniging=ver,
                           sporterboog__boogtype__in=boog_pks)
                   .values_list('pk', flat=True))

        # huidige leden mogen blijven ;-)
        ok2_pks = team.leden.values_list('pk', flat=True)

        ok_pks = list(ok1_pks) + list(ok2_pks)

        pks = list()
        for key in request.POST.keys():
            if key.startswith('deelnemer_'):
                try:
                    pk = int(key[10:10+7])      # afkappen voor de veiligheid
                except ValueError:
                    pass
                else:
                    if pk in ok_pks:
                        pks.append(pk)
                    # silently ignore bad pks
        # for

        pks = pks[:4]       # limiteer tot maximum 4 leden

        team.leden.clear()
        team.leden.add(*pks)

        bepaal_team_sterkte_en_klasse(team)

        if self.rol_nu == Rol.ROL_HWL:
            url = reverse('CompLaagRegio:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        else:
            url = reverse('CompLaagRegio:regio-teams', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class TeamsRegioInvallersView(UserPassesTestMixin, TemplateView):

    """ Geef de HWL een overzicht van de teams waarvoor de invallers gekoppeld kunnen worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_INVALLERS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def _get_deelcomp(self, deelcomp_pk) -> Regiocompetitie:

        # haal de gevraagde regiocompetitie op
        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie', 'regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             regio_organiseert_teamcompetitie=True,
                             regio=self.functie_nu.vereniging.regio))
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase_teams != 'F':
            raise Http404('Competitie is niet in de juiste fase')

        if self.rol_nu == Rol.ROL_WL:
            self.readonly = True

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        if not (1 <= deelcomp.huidige_team_ronde <= 7):
            raise Http404('Competitie ronde klopt niet')

        context['readonly'] = self.readonly     # voor WL

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(regiocompetitie=deelcomp,
                         vereniging=self.functie_nu.vereniging)
                 .order_by('volg_nr'))
        team_pks = [team.pk for team in teams]

        ronde_nr = deelcomp.huidige_team_ronde
        team_pk2ronde = dict()              # [team.pk] = RegiocompetitieRondeTeam
        deelnemer_pk2in_team = dict()       # [deelnemer.pk] = naam van team waar sporter in zit

        for ronde_team in (RegiocompetitieRondeTeam
                           .objects
                           .prefetch_related('deelnemers_feitelijk')
                           .select_related('team')
                           .annotate(feitelijke_deelnemers_count=Count('deelnemers_feitelijk'))
                           .filter(team__pk__in=team_pks,
                                   ronde_nr=ronde_nr)):

            team_pk2ronde[ronde_team.team.pk] = ronde_team

            for deelnemer in ronde_team.deelnemers_feitelijk.all():
                deelnemer_pk2in_team[deelnemer.pk] = ronde_team.team.maak_team_naam_kort()
            # for
        # for

        for team in teams:
            ronde_team = team_pk2ronde[team.pk]
            team.aantal = ronde_team.feitelijke_deelnemers_count

            if not self.readonly:
                team.url_koppelen = reverse('CompLaagRegio:teams-regio-invallers-koppelen',
                                            kwargs={'ronde_team_pk': ronde_team.pk})
        # for
        context['teams'] = teams

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'sporterboog__boogtype')
                      .prefetch_related('regiocompetitieteam_set')
                      .filter(regiocompetitie=deelcomp,
                              bij_vereniging=self.functie_nu.vereniging,
                              inschrijf_voorkeur_team=True)
                      .order_by('sporterboog__boogtype__volgorde',
                                '-ag_voor_team'))

        unsorted_deelnemers = list()
        for deelnemer in deelnemers:
            deelnemer.boog_str = deelnemer.sporterboog.boogtype.beschrijving
            deelnemer.naam_str = "[%s] %s" % (deelnemer.sporterboog.sporter.lid_nr,
                                              deelnemer.sporterboog.sporter.volledige_naam())

            gem = deelnemer.gemiddelde_begin_team_ronde
            gem_str = "%.3f" % gem
            deelnemer.gem_str = gem_str.replace('.', ',')

            tup = (-gem, deelnemer.sporterboog.sporter.lid_nr, deelnemer.pk, deelnemer)
            unsorted_deelnemers.append(tup)

            try:
                deelnemer.in_team_str = deelnemer_pk2in_team[deelnemer.pk]
            except KeyError:
                deelnemer.in_team_str = ''
        # for

        unsorted_deelnemers.sort()
        context['deelnemers'] = [tup[-1] for tup in unsorted_deelnemers]

        comp = deelcomp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (None, 'Team Invallers')
        )

        return context


class TeamsRegioInvallersKoppelLedenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL leden van zijn vereniging koppelen als invaller voor een team """

    template_name = TEMPLATE_TEAMS_INVALLERS_KOPPELEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            ronde_team_pk = int(kwargs['ronde_team_pk'][:6])        # afkappen voor de veiligheid
            ronde_team = (RegiocompetitieRondeTeam
                          .objects
                          .select_related('team',
                                          'team__regiocompetitie',
                                          'team__team_type')
                          .prefetch_related('team__team_type__boog_typen')
                          .get(pk=ronde_team_pk,
                               team__vereniging=self.functie_nu.vereniging))
        except (ValueError, RegiocompetitieRondeTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')

        team = ronde_team.team
        context['team'] = team
        context['deelcomp'] = deelcomp = team.regiocompetitie
        context['logboek'] = ronde_team.logboek

        # TODO: check competitie fase (E of F)

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .select_related('team',
                                       'team__team_type')
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk')
                       .filter(team__vereniging=self.functie_nu.vereniging,
                               ronde_nr=deelcomp.huidige_team_ronde))

        deelnemers_bezet_pks = list()

        ronde_team_nu = None
        for ronde_team in ronde_teams:
            if ronde_team.team == team:
                ronde_team_nu = ronde_team
            else:
                pks = list(ronde_team.deelnemers_feitelijk.values_list('pk', flat=True))
                deelnemers_bezet_pks.extend(pks)
        # for

        if not ronde_team_nu:
            raise Http404('Kan vastgestelde team leden niet ophalen')

        deelnemers_geselecteerd_pks = list(ronde_team_nu.deelnemers_geselecteerd.values_list('pk', flat=True))
        deelnemers_feitelijk_pks = list(ronde_team_nu.deelnemers_feitelijk.values_list('pk', flat=True))

        ronde_team_nu_afkorting = ronde_team_nu.team.team_type.afkorting

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp,
                              inschrijf_voorkeur_team=True,
                              bij_vereniging=self.functie_nu.vereniging,
                              sporterboog__boogtype__in=boog_pks)
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'sporterboog__boogtype')
                      .order_by('-gemiddelde_begin_team_ronde',
                                'sporterboog__pk'))

        unsorted_uitvallers = list()
        unsorted_bezet = list()
        unsorted_geen_ag = list()
        for deelnemer in deelnemers:
            gem_str = "%.3f" % deelnemer.gemiddelde_begin_team_ronde
            deelnemer.invaller_gem_str = gem_str.replace('.', ',')
            deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()

            if deelnemer.sporterboog.boogtype.afkorting != ronde_team_nu_afkorting:
                # vreemde vogel: BB in R team, LB in BB team, etc.
                # toon uitdrukkelijk het type boog voor deze sporters;
                # sporters ingeschreven met meerdere bogen worden zo duidelijk onderscheiden
                deelnemer.naam_str += ' (%s)' % deelnemer.sporterboog.boogtype.beschrijving

            if deelnemer.pk in deelnemers_geselecteerd_pks:
                deelnemer.origineel_team_lid = True
                gem_str = "%.3f" % deelnemer.gemiddelde_begin_team_ronde
                deelnemer.uitvaller_gem_str = gem_str.replace('.', ',')

                tup = (deelnemer.gemiddelde_begin_team_ronde, 0-deelnemer.pk, deelnemer)
                unsorted_uitvallers.append(tup)
            else:
                deelnemer.origineel_team_lid = False
                if deelnemer.ag_voor_team < 0.001:
                    tup = (deelnemer.sporterboog.sporter.lid_nr, deelnemer.sporterboog.pk, deelnemer)
                    unsorted_geen_ag.append(tup)
                    deelnemers_bezet_pks.append(deelnemer.pk)
                else:
                    if deelnemer.pk in deelnemers_bezet_pks:
                        tup = (deelnemer.gemiddelde_begin_team_ronde, 0-deelnemer.pk, deelnemer)
                        unsorted_bezet.append(tup)
        # for

        unsorted_uitvallers.sort(reverse=True)      # hoogste gemiddelde eerst

        if len(unsorted_geen_ag) > 0:
            unsorted_geen_ag.sort()     # op lid_nr
            context['geen_ag'] = [tup[-1] for tup in unsorted_geen_ag]

        if len(unsorted_bezet) > 0:
            unsorted_bezet.sort(reverse=True)
            context['bezet'] = [tup[-1] for tup in unsorted_bezet]

        # bouw een lijst van uitvallers
        #   elke uitvaller heeft een lijst van mogelijke invallers
        context['uitvallers'] = uitvallers = list()

        uniq_nr = 999000
        while len(unsorted_uitvallers) > 0:
            _, _, uitvaller = unsorted_uitvallers.pop(-1)               # begin bij de laagste
            group_str = "invaller_%s" % (1 + len(unsorted_uitvallers))  # laagste invaller heeft hoogste nummer
            invallers = list()
            tup = (uitvaller.naam_str, uitvaller.uitvaller_gem_str, group_str, invallers)
            uitvallers.insert(0, tup)

            zoek_checked = True

            # zet de sporter zelf bovenaan in het lijstje
            for deelnemer in deelnemers:
                # mag deze persoon invallen?
                if deelnemer.pk not in deelnemers_bezet_pks:
                    if deelnemer.pk == uitvaller.pk:
                        is_uitvaller = "1" if deelnemer.origineel_team_lid else "0"
                        id_invaller = group_str + '_door_%s' % deelnemer.pk
                        if deelnemer.pk in deelnemers_feitelijk_pks:
                            deelnemers_feitelijk_pks.remove(deelnemer.pk)
                            toon_checked = True
                        else:
                            toon_checked = False
                        zoek_checked = not toon_checked
                        tup = (is_uitvaller, deelnemer.invaller_gem_str, id_invaller, deelnemer.pk, deelnemer.naam_str,
                               toon_checked)
                        invallers.append(tup)
                        break
            # for

            for deelnemer in deelnemers:
                # mag deze persoon invallen?
                if deelnemer.pk not in deelnemers_bezet_pks:
                    if (deelnemer.pk != uitvaller.pk and
                            deelnemer.gemiddelde_begin_team_ronde <= uitvaller.gemiddelde_begin_team_ronde):
                        is_uitvaller = "1" if deelnemer.origineel_team_lid else "0"
                        id_invaller = group_str + '_door_%s' % deelnemer.pk
                        toon_checked = False
                        if zoek_checked and deelnemer.pk in deelnemers_feitelijk_pks:
                            toon_checked = True
                            zoek_checked = False
                            deelnemers_feitelijk_pks.remove(deelnemer.pk)
                        tup = (is_uitvaller, deelnemer.invaller_gem_str, id_invaller, deelnemer.pk, deelnemer.naam_str,
                               toon_checked)
                        invallers.append(tup)
            # for

            # voeg de optie "Geen invaller beschikbaar" toe
            tup = (False, "", group_str + "_door_geen", uniq_nr, "Geen invaller beschikbaar", zoek_checked)
            uniq_nr += 1
            invallers.append(tup)
        # while

        context['url_opslaan'] = reverse('CompLaagRegio:teams-regio-invallers-koppelen',
                                         kwargs={'ronde_team_pk': ronde_team_nu.pk})

        comp = deelcomp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagRegio:teams-regio-invallers', kwargs={'deelcomp_pk': deelcomp.pk}), 'Team Invallers'),
            (None, 'Invallers Koppelen')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            ronde_team_pk = int(kwargs['ronde_team_pk'][:6])        # afkappen voor de veiligheid
            ronde_team = (RegiocompetitieRondeTeam
                          .objects
                          .select_related('team')
                          .prefetch_related('deelnemers_geselecteerd')
                          .get(pk=ronde_team_pk,
                               team__vereniging=self.functie_nu.vereniging))
        except (ValueError, RegiocompetitieRondeTeam.DoesNotExist):
            raise Http404('Team ronde niet gevonden of niet van jouw vereniging')

        team = ronde_team.team
        deelcomp = team.regiocompetitie

        # TODO: check competitie fase

        # zoek uit wie 'bezet' zijn in een ander team
        deelnemers_bezet_pks = list()

        for ronde_team2 in (RegiocompetitieRondeTeam
                            .objects
                            .select_related('team')
                            .prefetch_related('deelnemers_geselecteerd',
                                              'deelnemers_feitelijk')
                            .exclude(team=team)
                            .filter(team__vereniging=self.functie_nu.vereniging,
                                    ronde_nr=deelcomp.huidige_team_ronde)):

            pks = list(ronde_team2.deelnemers_feitelijk.values_list('pk', flat=True))
            deelnemers_bezet_pks.extend(pks)
        # for

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)

        pk2gem = dict()     # kandidaat-deelnemer pk's en gemiddelde

        max_gem = list()
        for deelnemer in ronde_team.deelnemers_geselecteerd.all():
            max_gem.append(deelnemer.gemiddelde_begin_team_ronde)
            pk2gem[deelnemer.pk] = deelnemer.gemiddelde_begin_team_ronde
        # for

        # voorkomt problemen verderop
        if len(max_gem) == 0:
            raise Http404('Team is niet compleet')

        max_gem.sort(reverse=True)      # hoogste eerst

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp,
                              inschrijf_voorkeur_team=True,
                              bij_vereniging=self.functie_nu.vereniging,
                              sporterboog__boogtype__in=boog_pks,
                              ag_voor_team__gt=0.0))     # sporter moet een team AG hebben

        for deelnemer in deelnemers:
            if deelnemer.pk not in deelnemers_bezet_pks:
                if deelnemer.gemiddelde_begin_team_ronde <= max_gem[0]:
                    pk2gem[deelnemer.pk] = deelnemer.gemiddelde_begin_team_ronde
        # for

        # we hebben nu alle toegestane deelnemer pk's in pk2gem
        sel_pks = list()
        nr = 0
        while nr < len(max_gem):
            nr += 1

            sel_pk = request.POST.get('invaller_%s' % nr, '')
            try:
                sel_pk = int(str(sel_pk)[:6])       # afkappen voor de veiligheid
            except ValueError:
                raise Http404('Verkeerde parameters')

            # nummers 999000 en hoger worden gebruikt voor "geen invaller"
            if sel_pk < 999000:
                try:
                    gem1 = pk2gem[sel_pk]
                    gem2 = max_gem[len(sel_pks)]
                    if gem1 > gem2:
                        raise Http404('Selectie is te sterk: %.3f > %.3f' % (gem1, gem2))
                except KeyError:
                    raise Http404('Geen valide selectie')

                sel_pks.append(sel_pk)
        # while

        # sel_pks bevat de geaccepteerde feitelijke sporters
        # nog even iets in het logboek schrijven

        now = timezone.now()
        now = timezone.localtime(now)
        now_str = now.strftime("%Y-%m-%d %H:%M")

        account = get_account(request)
        wie_str = account.volledige_naam() + " (%s)" % account.username

        ronde_team.logboek += '\n\n[%s] Selectie is aangepast door %s:\n' % (now_str, wie_str)

        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog__sporter')
                          .filter(pk__in=sel_pks)):
            ronde_team.logboek += '   ' + str(deelnemer.sporterboog.sporter) + '\n'
        # for

        ronde_team.save(update_fields=['logboek'])

        ronde_team.deelnemers_feitelijk.set(sel_pks)

        # trigger een update van de team-scores
        update_uitslag_teamcompetitie()

        url = reverse('CompLaagRegio:teams-regio-invallers',
                      kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


# end of file
