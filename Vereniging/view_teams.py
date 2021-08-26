# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType, BoogType
from Competitie.models import (CompetitieKlasse, AG_NUL, DeelCompetitie, LAAG_REGIO,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_TYPE_TEAM_AG
from Score.operations import score_teams_ag_opslaan
import datetime


TEMPLATE_TEAMS_REGIO = 'vereniging/teams-regio.dtl'
TEMPLATE_TEAMS_REGIO_WIJZIG = 'vereniging/teams-regio-wijzig.dtl'
TEMPLATE_TEAMS_WIJZIG_AG = 'vereniging/teams-wijzig-ag.dtl'
TEMPLATE_TEAMS_KOPPELEN = 'vereniging/teams-koppelen.dtl'
TEMPLATE_TEAMS_INVALLERS = 'vereniging/teams-invallers.dtl'
TEMPLATE_TEAMS_INVALLERS_KOPPELEN = 'vereniging/teams-invallers-koppelen.dtl'
TEMPLATE_TEAMS_RK = 'vereniging/teams-rk.dtl'


def update_uitslag_teamcompetitie():
    # regiocomp_tussenstand moet getriggered worden
    # maak daarvoor een ScoreHist record aan, welke verwijst naar een fake Score record

    fake_scores = Score.objects.filter(schutterboog=None)
    if fake_scores.count() == 0:
        # fake Score heeft een fake SchutterBoog nodig
        boogtype = BoogType.objects.all()[0]

        fake_sb = SchutterBoog(boogtype=boogtype)
        fake_sb.save()

        fake_score = Score(
                        schutterboog=fake_sb,
                        waarde=0,
                        afstand_meter=0)
        fake_score.save()
    else:
        fake_score = fake_scores[0]

    ScoreHist(score=fake_score,
              oude_waarde=0,
              nieuwe_waarde=0,
              notitie="Trigger background task").save()


def bepaal_team_sterkte_en_klasse(team):
    """ gebruik AG van gekoppelde schutters om team aanvangsgemiddelde te berekenen
        en bepaal aan de hand daarvan de team wedstrijdklasse
    """
    ags = team.gekoppelde_schutters.values_list('ag_voor_team', flat=True)
    ags = list(ags)

    team.klasse = None

    if len(ags) >= 3:
        # bereken de team sterkte: de som van de 3 sterkste sporters
        ags.sort(reverse=True)
        ag = sum(ags[:3])

        # bepaal de wedstrijdklasse
        comp = team.deelcompetitie.competitie
        for klasse in (CompetitieKlasse
                       .objects
                       .filter(competitie=comp,
                               team__team_type=team.team_type)
                       .order_by('min_ag', '-team__volgorde')):  # oplopend AG (=hogere klasse later)
            if ag >= klasse.min_ag:
                team.klasse = klasse
        # for
    else:
        ag = AG_NUL

    team.aanvangsgemiddelde = ag
    team.save()


class TeamsRegioView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de regiocompetitie.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_REGIO
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL)

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
            raise Http404()

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'E':
            # staat niet meer open voor instellen regiocompetitie teams
            raise Http404('Competitie is niet in de juiste fase')

        self.readonly = (comp.fase > 'C')

        if self.rol_nu == Rollen.ROL_WL:
            self.readonly = True

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        now = timezone.now()
        einde = datetime.datetime(year=deelcomp.einde_teams_aanmaken.year,
                                  month=deelcomp.einde_teams_aanmaken.month,
                                  day=deelcomp.einde_teams_aanmaken.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        einde = timezone.make_aware(einde)
        mag_wijzigen = (now < einde) and not self.readonly
        context['mag_wijzigen'] = mag_wijzigen
        context['readonly'] = self.readonly

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
                 .annotate(gekoppelde_schutters_count=Count('gekoppelde_schutters'))
                 .order_by('volg_nr'))
        for obj in teams:
            obj.aantal = obj.gekoppelde_schutters_count
            obj.ag_str = "%05.1f" % (obj.aanvangsgemiddelde * aantal_pijlen)
            obj.ag_str = obj.ag_str.replace('.', ',')

            if mag_wijzigen:
                obj.url_wijzig = reverse('Vereniging:teams-regio-wijzig',
                                         kwargs={'deelcomp_pk': deelcomp.pk,
                                                 'team_pk': obj.pk})

            # koppelen == bekijken
            obj.url_koppelen = reverse('Vereniging:teams-regio-koppelen',
                                       kwargs={'team_pk': obj.pk})
        # for
        context['teams'] = teams

        if mag_wijzigen:
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
                                '-ag_voor_team'))
        for obj in deelnemers:
            obj.boog_str = obj.schutterboog.boogtype.beschrijving
            obj.naam_str = "[%s] %s" % (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.nhblid.volledige_naam())
            obj.ag_str = "%.3f" % obj.ag_voor_team
            obj.ag_str = obj.ag_str.replace('.', ',')

            try:
                team = obj.regiocompetitieteam_set.all()[0]
            except IndexError:
                pass
            else:
                obj.in_team_str = team.maak_team_naam_kort()

            if obj.ag_voor_team < 0.001:
                obj.rood_ag = True

            if obj.ag_voor_team_mag_aangepast_worden:
                obj.ag_str += " (handmatig)"
                if mag_wijzigen:
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
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_RCL)

    def _get_deelcomp(self, deelcomp_pk) -> DeelCompetitie:
        # haal de gevraagde deelcompetitie op

        if self.rol_nu == Rollen.ROL_HWL:
            regio = self.functie_nu.nhb_ver.regio
            max_fase = 'C'
        else:
            # RCL
            regio = self.functie_nu.nhb_regio
            max_fase = 'D'

        try:
            deelcomp_pk = int(deelcomp_pk[:6])     # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk,
                             is_afgesloten=False,
                             laag=LAAG_REGIO,                           # moet regiocompetitie zijn
                             regio_organiseert_teamcompetitie=True,
                             nhb_regio=regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if comp.fase > max_fase:
            # staat niet meer open voor instellen regiocompetitie teams
            raise Http404('Competitie is niet in de juiste fase')

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu == Rollen.ROL_RCL:
            raise Http404('Verkeerde rol')

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])
        ver = self.functie_nu.nhb_ver

        now = timezone.now()
        einde = datetime.datetime(year=deelcomp.einde_teams_aanmaken.year,
                                  month=deelcomp.einde_teams_aanmaken.month,
                                  day=deelcomp.einde_teams_aanmaken.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        einde = timezone.make_aware(einde)
        mag_wijzigen = (now <= einde)

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
            team = (RegiocompetitieTeam
                    .objects
                    .get(pk=team_pk,
                         deelcompetitie=deelcomp,
                         vereniging=ver))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')
        except KeyError:
            # dit is een nieuw team
            if not mag_wijzigen:
                raise Http404('Kan geen nieuw team meer aanmaken')

            team = RegiocompetitieTeam(
                            pk=0,
                            vereniging=self.functie_nu.nhb_ver,
                            team_type=teamtype_default)

        context['team'] = team

        for obj in teams:
            obj.actief = team.team_type == obj
        # for

        if mag_wijzigen:
            context['url_opslaan'] = reverse('Vereniging:teams-regio-wijzig',
                                             kwargs={'deelcomp_pk': deelcomp.pk,
                                                     'team_pk': team.pk})

            if team.pk > 0:
                context['url_verwijderen'] = context['url_opslaan']
        else:
            context['readonly'] = True

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        if self.rol_nu == Rollen.ROL_HWL:
            ver = self.functie_nu.nhb_ver

            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.einde_teams_aanmaken.year,
                                      month=deelcomp.einde_teams_aanmaken.month,
                                      day=deelcomp.einde_teams_aanmaken.day,
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

        try:
            team_pk = int(kwargs['team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
            raise Http404()

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
                raise Http404('Maximum van 10 teams is bereikt')

            afkorting = request.POST.get('team_type', '')
            try:
                team_type = TeamType.objects.get(afkorting=afkorting)
            except TeamType.DoesNotExist:
                raise Http404()

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
                             deelcompetitie=deelcomp))
            except RegiocompetitieTeam.DoesNotExist:
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

        if self.rol_nu == Rollen.ROL_HWL:
            url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        else:
            url = reverse('Competitie:regio-teams', kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


class WijzigTeamAGView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_WIJZIG_AG
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL)

    def _mag_wijzigen_of_404(self, deelnemer):
        ver = deelnemer.bij_vereniging
        if self.rol_nu == Rollen.ROL_HWL:
            # HWL
            if ver != self.functie_nu.nhb_ver:
                raise PermissionDenied('Niet lid van jouw vereniging')
        else:
            # RCL
            if ver.regio != self.functie_nu.nhb_regio:
                raise PermissionDenied('Niet lid van een vereniging in jouw regio')

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
                                         'bij_vereniging',
                                         'deelcompetitie__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        context['deelnemer'] = deelnemer

        # controleer dat deze deelnemer bekeken en gewijzigd mag worden
        self._mag_wijzigen_of_404(deelnemer)

        deelnemer.naam_str = deelnemer.schutterboog.nhblid.volledige_naam()
        deelnemer.boog_str = deelnemer.schutterboog.boogtype.beschrijving
        deelnemer.ag_str = '%.3f' % deelnemer.ag_voor_team

        ag_hist = (ScoreHist
                   .objects
                   .filter(score__schutterboog=deelnemer.schutterboog,
                           score__afstand_meter=deelnemer.deelcompetitie.competitie.afstand,
                           score__type=SCORE_TYPE_TEAM_AG)
                   .order_by('-when'))
        for obj in ag_hist:
            obj.oude_waarde /= 1000
            obj.nieuwe_waarde /= 1000
            obj.oude_waarde_str = "%.3f" % obj.oude_waarde
            obj.nieuwe_waarde_str = "%.3f" % obj.nieuwe_waarde
        # for
        context['ag_hist'] = ag_hist

        context['url_opslaan'] = reverse('Vereniging:wijzig-ag',
                                         kwargs={'deelnemer_pk': deelnemer.pk})

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
            raise Http404()

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

            score_teams_ag_opslaan(
                    deelnemer.schutterboog,
                    deelnemer.deelcompetitie.competitie.afstand,
                    nieuw_ag,
                    request.user,
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
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_RCL)

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
                    .get(pk=team_pk))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            ver = self.functie_nu.nhb_ver
            if team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            # RCL
            ver = team.vereniging

        context['team'] = team

        context['deelcomp'] = deelcomp = team.deelcompetitie

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if self.rol_nu == Rollen.ROL_HWL:
            context['readonly'] = readonly = (comp.fase > 'C')
            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.einde_teams_aanmaken.year,
                                      month=deelcomp.einde_teams_aanmaken.month,
                                      day=deelcomp.einde_teams_aanmaken.day,
                                      hour=0,
                                      minute=0,
                                      second=0)
            einde = timezone.make_aware(einde)
            mag_wijzigen = (now <= einde) and not readonly
        else:
            # RCL
            context['readonly'] = readonly = (comp.fase > 'D')
            mag_wijzigen = True

        context['mag_wijzigen'] = mag_wijzigen

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        if deelcomp.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        team.ag_str = "%5.1f" % (team.aanvangsgemiddelde * aantal_pijlen)

        if mag_wijzigen:
            pks = team.gekoppelde_schutters.values_list('pk', flat=True)

            deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp,
                                  inschrijf_voorkeur_team=True,
                                  bij_vereniging=ver,
                                  schutterboog__boogtype__in=boog_pks)
                          .annotate(in_team_count=Count('regiocompetitieteam'))
                          .select_related('schutterboog',
                                          'schutterboog__nhblid',
                                          'schutterboog__boogtype')
                          .order_by('-ag_voor_team'))
            for obj in deelnemers:
                obj.sel_str = "deelnemer_%s" % obj.pk
                obj.naam_str = "[%s] %s" % (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.nhblid.volledige_naam())
                obj.boog_str = obj.schutterboog.boogtype.beschrijving
                obj.ag_str = "%.3f" % obj.ag_voor_team
                obj.blokkeer = (obj.ag_voor_team < 0.001)
                obj.geselecteerd = (obj.pk in pks)          # vinkje zetten: gekoppeld aan dit team
                if not obj.geselecteerd:
                    if obj.in_team_count > 0:
                        obj.blokkeer = True                 # niet te selecteren: gekoppeld aan een ander team
            # for
            context['deelnemers'] = deelnemers

            context['url_opslaan'] = reverse('Vereniging:teams-regio-koppelen',
                                             kwargs={'team_pk': team.pk})
        else:
            context['gekoppeld'] = gekoppeld = (team
                                                .gekoppelde_schutters
                                                .select_related('schutterboog',
                                                                'schutterboog__nhblid',
                                                                'schutterboog__boogtype')
                                                .order_by('-ag_voor_team'))
            for obj in gekoppeld:
                obj.naam_str = "[%s] %s" % (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.nhblid.volledige_naam())
                obj.boog_str = obj.schutterboog.boogtype.beschrijving
                obj.ag_str = "%.3f" % obj.ag_voor_team
            # for

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
                    .get(pk=team_pk))
        except (ValueError, RegiocompetitieTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            ver = self.functie_nu.nhb_ver
            if team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = team.vereniging

        deelcomp = team.deelcompetitie

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if self.rol_nu == Rollen.ROL_HWL:
            readonly = (comp.fase > 'C')
            now = timezone.now()
            einde = datetime.datetime(year=deelcomp.einde_teams_aanmaken.year,
                                      month=deelcomp.einde_teams_aanmaken.month,
                                      day=deelcomp.einde_teams_aanmaken.day,
                                      hour=0,
                                      minute=0,
                                      second=0)
            einde = timezone.make_aware(einde)
            mag_wijzigen = (now <= einde) and not readonly
        else:
            # RCL
            readonly = (comp.fase > 'D')
            mag_wijzigen = not readonly

        if not mag_wijzigen:
            raise Http404('Voorbij de einddatum voor wijzigingen')

        # toegestane boogtypen en schutters
        boog_pks = team.team_type.boog_typen.values_list('pk', flat=True)
        bezet_pks = team.gekoppelde_schutters.values_list('pk', flat=True)

        # leden die nog niet in een team zitten
        ok1_pks = (RegioCompetitieSchutterBoog
                   .objects
                   .exclude(pk__in=bezet_pks)
                   .filter(deelcompetitie=team.deelcompetitie,
                           inschrijf_voorkeur_team=True,
                           ag_voor_team__gte=1.0,
                           bij_vereniging=ver,
                           schutterboog__boogtype__in=boog_pks)
                   .values_list('pk', flat=True))

        # huidige leden mogen blijven ;-)
        ok2_pks = team.gekoppelde_schutters.values_list('pk', flat=True)

        ok_pks = list(ok1_pks) + list(ok2_pks)

        pks = list()
        for key in request.POST.keys():
            if key.startswith('deelnemer_'):
                try:
                    pk = int(key[10:])
                except ValueError:
                    pass
                else:
                    if pk in ok_pks:
                        pks.append(pk)
                    # silently ignore bad pks
        # for

        team.gekoppelde_schutters.clear()
        team.gekoppelde_schutters.add(*pks)

        bepaal_team_sterkte_en_klasse(team)

        if self.rol_nu == Rollen.ROL_HWL:
            url = reverse('Vereniging:teams-regio', kwargs={'deelcomp_pk': deelcomp.pk})
        else:
            url = reverse('Competitie:regio-teams', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class TeamsRegioInvallersView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de invallers van zijn teams opgeven.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TEAMS_INVALLERS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL)

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
            raise Http404()

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase != 'E':
            # staat niet meer open voor instellen regiocompetitie teams
            raise Http404('Competitie is niet in de juiste fase')

        if self.rol_nu == Rollen.ROL_WL:
            self.readonly = True

        return deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp'] = deelcomp = self._get_deelcomp(kwargs['deelcomp_pk'])

        if not (1 <= deelcomp.huidige_team_ronde <= 7):
            raise Http404('Competitie ronde klopt niet')

        context['readonly'] = self.readonly

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('vereniging',
                                 'team_type')
                 .filter(deelcompetitie=deelcomp,
                         vereniging=self.functie_nu.nhb_ver)
                 .order_by('volg_nr'))
        team_pks = [team.pk for team in teams]

        ronde_nr = deelcomp.huidige_team_ronde
        team_pk2ronde = dict()
        deelnemer_pk2in_team = dict()

        for ronde_team in (RegiocompetitieRondeTeam
                           .objects
                           .prefetch_related('deelnemers_feitelijk')
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
                team.url_koppelen = reverse('Vereniging:teams-regio-invallers-koppelen',
                                            kwargs={'ronde_team_pk': ronde_team.pk})
        # for
        context['teams'] = teams

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
                                '-ag_voor_team'))

        unsorted_deelnemers = list()
        for deelnemer in deelnemers:
            deelnemer.boog_str = deelnemer.schutterboog.boogtype.beschrijving
            deelnemer.naam_str = "[%s] %s" % (deelnemer.schutterboog.nhblid.nhb_nr, deelnemer.schutterboog.nhblid.volledige_naam())

            if deelnemer.aantal_scores == 0:
                vsg = deelnemer.ag_voor_team
            else:
                vsg = deelnemer.gemiddelde
            vsg_str = "%.3f" % vsg
            deelnemer.vsg_str = vsg_str.replace('.', ',')

            tup = (-vsg, deelnemer.schutterboog.nhblid.nhb_nr, deelnemer.pk, deelnemer)
            unsorted_deelnemers.append(tup)

            try:
                deelnemer.in_team_str = deelnemer_pk2in_team[deelnemer.pk]
            except KeyError:
                deelnemer.in_team_str = ''
        # for

        unsorted_deelnemers.sort()
        context['deelnemers'] = [tup[-1] for tup in unsorted_deelnemers]

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class TeamsRegioInvallersKoppelLedenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL leden van zijn vereniging koppelen als invaller voor een team """

    template_name = TEMPLATE_TEAMS_INVALLERS_KOPPELEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            ronde_team_pk = int(kwargs['ronde_team_pk'][:6])
            ronde_team = (RegiocompetitieRondeTeam
                          .objects
                          .select_related('team',
                                          'team__deelcompetitie',
                                          'team__team_type')
                          .prefetch_related('team__team_type__boog_typen')
                          .get(pk=ronde_team_pk,
                               team__vereniging=self.functie_nu.nhb_ver))
        except (ValueError, RegiocompetitieRondeTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')

        team = ronde_team.team
        context['team'] = team
        context['deelcomp'] = deelcomp = team.deelcompetitie
        context['logboek'] = ronde_team.logboek

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .select_related('team')
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk')
                       .filter(team__vereniging=self.functie_nu.nhb_ver,
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

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              inschrijf_voorkeur_team=True,
                              bij_vereniging=self.functie_nu.nhb_ver,
                              schutterboog__boogtype__in=boog_pks)
                      .select_related('schutterboog',
                                      'schutterboog__nhblid',
                                      'schutterboog__boogtype')
                      .order_by('-gemiddelde_begin_team_ronde', 'schutterboog__pk'))

        unsorted_uitvallers = list()
        unsorted_bezet = list()
        for deelnemer in deelnemers:
            gem_str = "%.3f" % deelnemer.gemiddelde_begin_team_ronde
            deelnemer.invaller_gem_str = gem_str.replace('.', ',')
            deelnemer.naam_str = "[%s] %s" % (deelnemer.schutterboog.nhblid.nhb_nr, deelnemer.schutterboog.nhblid.volledige_naam())

            if deelnemer.pk in deelnemers_geselecteerd_pks:
                deelnemer.origineel_team_lid = True
                gem_str = "%.3f" % deelnemer.gemiddelde_begin_team_ronde
                deelnemer.uitvaller_gem_str = gem_str.replace('.', ',')

                tup = (deelnemer.gemiddelde_begin_team_ronde, 0-deelnemer.pk, deelnemer)
                unsorted_uitvallers.append(tup)
            else:
                deelnemer.origineel_team_lid = False
                if deelnemer.pk in deelnemers_bezet_pks:
                    tup = (deelnemer.gemiddelde_begin_team_ronde, 0-deelnemer.pk, deelnemer)
                    unsorted_bezet.append(tup)
        # for

        unsorted_uitvallers.sort(reverse=True)      # hoogste gemiddelde eerst

        if len(unsorted_bezet) > 0:
            unsorted_bezet.sort(reverse=True)
            context['bezet'] = [tup[-1] for tup in unsorted_bezet]

        # bouw een lijst van uitvallers
        #   elke uitvaller heeft een lijst van mogelijke invallers
        context['uitvallers'] = uitvallers = list()

        uniq_nr = 999000
        while len(unsorted_uitvallers) > 0:
            _, _, uitvaller = unsorted_uitvallers.pop(-1)              # begin bij de laagste
            group_str = "invaller_%s" % (1 + len(unsorted_uitvallers))  # laagste invaller heeft hoogste nummer
            invallers = list()
            tup = (uitvaller.naam_str, uitvaller.uitvaller_gem_str, group_str, invallers)
            uitvallers.insert(0, tup)

            zoek_checked = True
            for deelnemer in deelnemers:
                # mag deze persoon invallen?
                if deelnemer.pk == uitvaller.pk or deelnemer.gemiddelde_begin_team_ronde <= uitvaller.gemiddelde_begin_team_ronde:
                    is_uitvaller = "1" if deelnemer.origineel_team_lid else "0"
                    id_invaller = group_str + '_door_%s' % deelnemer.pk
                    toon_checked = False
                    if zoek_checked and deelnemer.pk in deelnemers_feitelijk_pks:
                        toon_checked = True
                        zoek_checked = False
                        deelnemers_feitelijk_pks.remove(deelnemer.pk)
                    tup = (is_uitvaller, deelnemer.invaller_gem_str, id_invaller, deelnemer.pk, deelnemer.naam_str, toon_checked)
                    invallers.append(tup)
            # for

            # voeg de optie "Geen invaller" toe
            tup = (False, "", group_str + "_door_geen", uniq_nr, "Geen invaller", zoek_checked)
            uniq_nr += 1
            invallers.append(tup)
        # while

        context['url_opslaan'] = reverse('Vereniging:teams-regio-invallers-koppelen',
                                         kwargs={'ronde_team_pk': ronde_team_nu.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            ronde_team_pk = int(kwargs['ronde_team_pk'][:6])
            ronde_team = (RegiocompetitieRondeTeam
                          .objects
                          .select_related('team')
                          .prefetch_related('deelnemers_geselecteerd')
                          .get(pk=ronde_team_pk,
                               team__vereniging=self.functie_nu.nhb_ver))
        except (ValueError, RegiocompetitieRondeTeam.DoesNotExist):
            raise Http404('Team ronde niet gevonden of niet van jouw vereniging')

        team = ronde_team.team
        deelcomp = team.deelcompetitie

        # zoek uit wie 'bezet' zijn in een ander team
        deelnemers_bezet_pks = list()

        for ronde_team2 in (RegiocompetitieRondeTeam
                            .objects
                            .select_related('team')
                            .prefetch_related('deelnemers_geselecteerd',
                                              'deelnemers_feitelijk')
                            .exclude(team=team)
                            .filter(team__vereniging=self.functie_nu.nhb_ver,
                                    ronde_nr=deelcomp.huidige_team_ronde)):

            pks = list(ronde_team2.deelnemers_feitelijk.values_list('pk', flat=True))
            deelnemers_bezet_pks.extend(pks)
        # for

        boog_typen = team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)

        pk2gem = dict()     # kandidaat deelnemer pk's en gemiddelde

        max_gem = list()
        for deelnemer in ronde_team.deelnemers_geselecteerd.all():
            max_gem.append(deelnemer.gemiddelde_begin_team_ronde)
            pk2gem[deelnemer.pk] = deelnemer.gemiddelde_begin_team_ronde
        # for

        # voorkomt problemen verderop
        if len(max_gem) == 0:
            raise Http404('Team is niet compleet')

        max_gem.sort(reverse=True)      # hoogste eerst

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              inschrijf_voorkeur_team=True,
                              bij_vereniging=self.functie_nu.nhb_ver,
                              schutterboog__boogtype__in=boog_pks))

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

        account = request.user
        wie_str = account.volledige_naam() + " (%s)" % account.username

        ronde_team.logboek += '\n\n[%s] Selectie is aangepast door %s:\n' % (now_str, wie_str)

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('schutterboog__nhblid')
                          .filter(pk__in=sel_pks)):
            ronde_team.logboek += '   ' + str(deelnemer.schutterboog.nhblid) + '\n'
        # for

        ronde_team.save(update_fields=['logboek'])

        ronde_team.deelnemers_feitelijk.set(sel_pks)

        # trigger een update van de team scores
        update_uitslag_teamcompetitie()

        url = reverse('Vereniging:teams-regio-invallers',
                      kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(url)


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

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        # ver = functie_nu.nhb_ver

        menu_dynamics(self.request, context, actief='vereniging')
        return context

# end of file
