# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.models import (AG_NUL, DeelCompetitie, LAAG_RK, CompetitieKlasse, CompetitieTeamKlasse,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog, KampioenschapTeam)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
import datetime


TEMPLATE_COMPRAYON_VERTEAMS = 'comprayon/hwl-teams.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_WIJZIG = 'comprayon/hwl-teams-wijzig.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_KOPPELEN = 'comprayon/hwl-teams-koppelen.dtl'


def bepaal_regioschutter_gemiddelde_voor_rk_teams(deelnemer):
    if deelnemer.aantal_scores >= 3:
        ag = deelnemer.gemiddelde
        bron = "VSG na %s scores" % deelnemer.aantal_scores
    else:
        if deelnemer.ag_voor_team > 0.0:
            ag = deelnemer.ag_voor_team
            bron = "Team AG"
        else:
            ag = deelnemer.ag_voor_indiv
            bron = "Individueel AG"

    return ag, bron


def bepaal_rk_team_tijdelijke_sterkte_en_klasse(rk_team, open_inschrijving):
    """ gebruik AG/VSG van gekoppelde schutters om team aanvangsgemiddelde te berekenen
        en bepaal aan de hand daarvan de team wedstrijdklasse
    """

    ags = list()
    if open_inschrijving:
        for deelnemer in rk_team.tijdelijke_schutters.all():
            ag, _ = bepaal_regioschutter_gemiddelde_voor_rk_teams(deelnemer)
            ags.append(ag)
        # for
    else:
        for deelnemer in rk_team.gekoppelde_schutters.all():
            ags.append(deelnemer.gemiddelde)
        # for

    rk_team.klasse = None       # wordt later bepaald, als de teams al bevroren zijn

    if len(ags) >= 3:
        # bereken de team sterkte: de som van de 3 sterkste sporters
        ags.sort(reverse=True)
        rk_team.aanvangsgemiddelde = sum(ags[:3])
    else:
        rk_team.aanvangsgemiddelde = AG_NUL

    rk_team.save(update_fields=['aanvangsgemiddelde', 'klasse'])


class TeamsRkView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de rayonkampioenschappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_VERTEAMS
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
            raise Http404('Competitie niet gevonden')

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if not ('E' <= comp.fase <= 'K'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase 1')

        vanaf = comp.eerste_wedstrijd + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase 2')

        deelcomp.open_inschrijving = comp.fase <= 'G'       # regio vs RK fase

        deelcomp.datum_einde_knutselen_teams_rk_bk = comp.datum_klassengrenzen_rk_bk_teams

        return deelcomp

    def _get_rk_teams(self, deelcomp_rk, is_vastgesteld):

        if deelcomp_rk.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        if deelcomp_rk.open_inschrijving:
            # open inschrijving RK
            rk_teams = (KampioenschapTeam
                        .objects
                        .select_related('vereniging',
                                        'team_type')
                        .filter(deelcompetitie=deelcomp_rk,
                                vereniging=self.functie_nu.nhb_ver)
                        .annotate(schutters_count=Count('tijdelijke_schutters'))
                        .order_by('volg_nr'))

        else:
            # team deelnemers bestaat uit gerechtigde RK deelnemers
            rk_teams = (KampioenschapTeam
                        .objects
                        .select_related('vereniging',
                                        'team_type')
                        .filter(deelcompetitie=deelcomp_rk,
                                vereniging=self.functie_nu.nhb_ver)
                        .annotate(schutters_count=Count('gekoppelde_schutters'))
                        .order_by('volg_nr'))

        for rk_team in rk_teams:
            rk_team.aantal = rk_team.schutters_count
            rk_team.ag_str = "%05.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
            rk_team.ag_str = rk_team.ag_str.replace('.', ',')

            if not is_vastgesteld:
                rk_team.url_wijzig = reverse('CompRayon:teams-rk-wijzig',
                                             kwargs={'rk_deelcomp_pk': deelcomp_rk.pk,
                                                     'rk_team_pk': rk_team.pk})

            # koppelen == bekijken
            rk_team.url_koppelen = reverse('CompRayon:teams-rk-koppelen',
                                           kwargs={'rk_team_pk': rk_team.pk})
        # for

        return rk_teams

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.nhb_ver

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp_rk'] = deelcomp_rk = self._get_deelcomp_rk(kwargs['rk_deelcomp_pk'])

        context['rk_bk_klassen_vastgesteld'] = is_vastgesteld = deelcomp_rk.competitie.klassengrenzen_vastgesteld_rk_bk

        context['rk_teams'] = self._get_rk_teams(deelcomp_rk, is_vastgesteld)

        if not is_vastgesteld:
            context['url_nieuw_team'] = reverse('CompRayon:teams-rk-nieuw',
                                                kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

        comp = deelcomp_rk.competitie
        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, comp.beschrijving.replace(' competitie', '')),
            (None, 'Teams RK'),
        )

        menu_dynamics(self.request, context)
        return context


class WijzigRKTeamsView(UserPassesTestMixin, TemplateView):

    """ laat de HWL een nieuw team aanmaken of een bestaand team wijzigen voor het RK
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_VERTEAMS_WIJZIG
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
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie',
                                           'nhb_rayon')
                           .get(pk=deelcomp_pk,
                                is_afgesloten=False,
                                laag=LAAG_RK,                           # moet RK zijn
                                nhb_rayon=self.functie_nu.nhb_ver.regio.rayon))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp = deelcomp_rk.competitie
        comp.bepaal_fase()

        if not ('E' <= comp.fase <= 'J'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase 1')

        vanaf = comp.eerste_wedstrijd + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase 2')

        return deelcomp_rk

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de deelcompetitie waar de regio teams voor in kunnen stellen
        context['deelcomp_rk'] = deelcomp_rk = self._get_deelcomp_rk(kwargs['rk_deelcomp_pk'])
        ver = self.functie_nu.nhb_ver
        comp = deelcomp_rk.competitie

        teamtype_default = None
        context['opt_team_type'] = teamtypes = CompetitieTeamKlasse.objects.filter(competitie=comp).distinct('team_afkorting').order_by('volgorde')
        for teamtype in teamtypes:
            teamtype.choice_name = teamtype.team_afkorting
            if teamtype.team_afkorting[0] == 'R':        # R or R2
                teamtype_default = teamtype
        # for

        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .get(pk=rk_team_pk,
                            deelcompetitie=deelcomp_rk,
                            vereniging=ver))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')
        except KeyError:
            # dit is een nieuw rk_team
            rk_team = KampioenschapTeam(
                            pk=0,
                            vereniging=self.functie_nu.nhb_ver,
                            team_type=teamtype_default)

        context['rk_team'] = rk_team

        for obj in teamtypes:
            obj.actief = rk_team.team_type == obj
        # for

        context['url_opslaan'] = reverse('CompRayon:teams-rk-wijzig',
                                         kwargs={'rk_deelcomp_pk': deelcomp_rk.pk,
                                                 'rk_team_pk': rk_team.pk})

        if rk_team.pk > 0:
            context['url_verwijderen'] = context['url_opslaan']

        comp = deelcomp_rk.competitie
        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, comp.beschrijving.replace(' competitie', '')),
            (reverse('CompRayon:teams-rk', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk}), 'Teams RK'),
            (None, 'Wijzig team')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        deelcomp = self._get_deelcomp_rk(kwargs['rk_deelcomp_pk'])
        comp = deelcomp.competitie
        ver = self.functie_nu.nhb_ver

        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
            raise Http404('Slechte parameter')

        # default = terug naar het overzicht van de Teams RK pagina
        url = reverse('CompRayon:teams-rk',
                      kwargs={'rk_deelcomp_pk': deelcomp.pk})

        if rk_team_pk == 0:
            # nieuw rk_team
            volg_nrs = (KampioenschapTeam
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                vereniging=ver)
                        .values_list('volg_nr', flat=True))
            volg_nrs = list(volg_nrs)
            volg_nrs.append(0)
            next_nr = max(volg_nrs) + 1

            if len(volg_nrs) > 25:
                # te veel teams
                raise Http404('Maximum van 25 teams is bereikt')

            afkorting = request.POST.get('team_type', '')
            try:
                klasse = (CompetitieKlasse
                          .objects
                          .select_related('team__team_type')
                          .filter(competitie=comp,
                                  team__afkorting=afkorting))[0]
                team_type = klasse.team.team_type
            except (IndexError, TeamType.DoesNotExist):
                raise Http404('Onbekend team type')

            rk_team = KampioenschapTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=team_type,
                            team_naam=' ')
            rk_team.save()

            verwijderen = False

            # na aanmaken meteen door naar de 'koppelen' pagina
            url = reverse('CompRayon:teams-rk-koppelen',
                          kwargs={'rk_team_pk': rk_team.pk})
        else:
            try:
                rk_team = (KampioenschapTeam
                           .objects
                           .select_related('team_type')
                           .get(pk=rk_team_pk,
                                deelcompetitie=deelcomp))
            except KampioenschapTeam.DoesNotExist:
                raise Http404('Team bestaat niet')

            if rk_team.vereniging != self.functie_nu.nhb_ver:
                raise Http404('Team is niet van jouw vereniging')

            verwijderen = request.POST.get('verwijderen', None) is not None

            if not verwijderen:
                afkorting = request.POST.get('team_type', '')
                if rk_team.team_type.afkorting != afkorting:
                    try:
                        team_type = TeamType.objects.get(afkorting=afkorting)
                    except TeamType.DoesNotExist:
                        raise Http404('Onbekend team type')

                    rk_team.team_type = team_type
                    rk_team.aanvangsgemiddelde = 0.0
                    rk_team.klasse = None
                    rk_team.save()

                    # verwijder eventueel gekoppelde sporters bij wijziging rk_team type,
                    # om verkeerde boog typen te voorkomen
                    rk_team.tijdelijke_schutters.clear()
                    rk_team.gekoppelde_schutters.clear()
                    # feitelijke schutters wordt pas later gebruikt

        if not verwijderen:
            team_naam = request.POST.get('team_naam', '')
            team_naam = team_naam.strip()
            if rk_team.team_naam != team_naam:
                if team_naam == '':
                    team_naam = "%s-%s" % (ver.ver_nr, rk_team.volg_nr)

                rk_team.team_naam = team_naam
                rk_team.save()
        else:
            rk_team.delete()

        return HttpResponseRedirect(url)


class RKTeamsKoppelLedenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL leden van zijn vereniging koppelen aan een team (of alleen bekijken) """

    template_name = TEMPLATE_COMPRAYON_VERTEAMS_KOPPELEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_RKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het rk_team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('deelcompetitie',
                                       'deelcompetitie__competitie',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            ver = self.functie_nu.nhb_ver
            if rk_team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = rk_team.vereniging

        context['rk_team'] = rk_team

        context['deelcomp_rk'] = deelcomp_rk = rk_team.deelcompetitie

        comp = deelcomp_rk.competitie
        comp.bepaal_fase()

        context['alleen_bekijken'] = alleen_bekijken = (comp.fase >= 'K')

        if not ('E' <= comp.fase <= 'L'):       # vanaf fase K kunnen invallers gekoppeld worden
            raise Http404('Competitie is niet in de juiste fase')

        boog_typen = rk_team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        if deelcomp_rk.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        ag_str = "%05.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
        rk_team.ag_str = ag_str.replace('.', ',')

        if comp.fase <= 'G':
            # alle leden van de vereniging die meedoen aan de regiocompetitie mogen gekozen worden

            context['onder_voorbehoud'] = True

            pks = rk_team.tijdelijke_schutters.values_list('pk', flat=True)

            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('tijdelijke_schutters')
                         .values_list('tijdelijke_schutters__pk', flat=True))

            deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .filter(deelcompetitie__competitie=comp,
                                  # inschrijf_voorkeur_team=True,
                                  bij_vereniging=ver,
                                  sporterboog__boogtype__in=boog_pks)
                          .exclude(indiv_klasse__is_aspirant_klasse=True)            # geen aspiranten
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype')
                          .order_by('-ag_voor_team'))

            for obj in deelnemers:
                obj.sel_str = "deelnemer_%s" % obj.pk
                obj.naam_str = "[%s] %s" % (obj.sporterboog.sporter.lid_nr, obj.sporterboog.sporter.volledige_naam())
                obj.boog_str = obj.sporterboog.boogtype.beschrijving

                ag, obj.ag_bron = bepaal_regioschutter_gemiddelde_voor_rk_teams(obj)
                ag_str = "%.3f" % ag
                obj.ag_str = ag_str.replace('.', ',')

                obj.blokkeer = False
                obj.geselecteerd = (obj.pk in pks)          # vinkje zetten: gekoppeld aan dit rk_team
                if not obj.geselecteerd:
                    if obj.pk in bezet_pks:
                        obj.blokkeer = True                 # niet te selecteren: gekoppeld aan een ander rk_team
            # for
        else:
            # alleen gerechtigde RK deelnemers mogen gekozen worden
            pks = rk_team.gekoppelde_schutters.values_list('pk', flat=True)

            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(deelcompetitie=deelcomp_rk,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('gekoppelde_schutters')
                         .values_list('gekoppelde_schutters__pk', flat=True))

            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp_rk,
                                  bij_vereniging=ver,
                                  sporterboog__boogtype__in=boog_pks)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype')
                          .order_by('-gemiddelde'))

            for obj in deelnemers:
                obj.sel_str = "deelnemer_%s" % obj.pk
                obj.naam_str = "[%s] %s" % (obj.sporterboog.sporter.lid_nr, obj.sporterboog.sporter.volledige_naam())
                obj.boog_str = obj.sporterboog.boogtype.beschrijving

                ag, obj.ag_bron = obj.gemiddelde, "Eindgemiddelde regiocompetitie"
                ag_str = "%.3f" % ag
                obj.ag_str = ag_str.replace('.', ',')

                obj.blokkeer = False
                obj.geselecteerd = (obj.pk in pks)          # vinkje zetten: gekoppeld aan dit rk_team
                if not obj.geselecteerd:
                    if obj.pk in bezet_pks:
                        obj.blokkeer = True                 # niet te selecteren: gekoppeld aan een ander rk_team
            # for

        context['deelnemers'] = deelnemers

        if not alleen_bekijken:
            context['url_opslaan'] = reverse('CompRayon:teams-rk-koppelen',
                                             kwargs={'rk_team_pk': rk_team.pk})

        comp = deelcomp_rk.competitie
        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, comp.beschrijving.replace(' competitie', '')),
            (reverse('CompRayon:teams-rk', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk}), 'Teams RK'),
            (None, 'Koppel teamleden')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('deelcompetitie',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            ver = self.functie_nu.nhb_ver
            if rk_team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = rk_team.vereniging

        deelcomp_rk = rk_team.deelcompetitie

        comp = deelcomp_rk.competitie
        comp.bepaal_fase()
        if not ('E' <= comp.fase <= 'J'):
            raise Http404('Competitie is niet in de juiste fase')

        open_inschrijving = comp.fase <= 'G'        # regio vs RK fase

        # toegestane boogtypen en schutters
        boog_pks = rk_team.team_type.boog_typen.values_list('pk', flat=True)

        if open_inschrijving:
            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(deelcompetitie=deelcomp_rk,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('tijdelijke_schutters')
                         .values_list('tijdelijke_schutters__pk', flat=True))

            ok_pks = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie__competitie=comp,
                              bij_vereniging=ver,
                              sporterboog__boogtype__in=boog_pks)
                      .values_list('pk', flat=True))

        else:
            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(deelcompetitie=deelcomp_rk,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('gekoppelde_schutters')
                         .values_list('gekoppelde_schutters__pk', flat=True))

            ok_pks = (KampioenschapSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp_rk,
                              bij_vereniging=ver,
                              sporterboog__boogtype__in=boog_pks)
                      .values_list('pk', flat=True))

        pks = list()
        for key in request.POST.keys():
            if key.startswith('deelnemer_'):
                try:
                    pk = int(key[10:10+6])      # afkappen voor de veiligheid
                except ValueError:
                    pass
                else:
                    if pk in ok_pks and pk not in bezet_pks:
                        pks.append(pk)
                    # silently ignore bad pks
        # for

        if open_inschrijving:
            rk_team.tijdelijke_schutters.clear()
            rk_team.tijdelijke_schutters.add(*pks)
        else:
            rk_team.gekoppelde_schutters.clear()
            rk_team.gekoppelde_schutters.add(*pks)

        bepaal_rk_team_tijdelijke_sterkte_en_klasse(rk_team, open_inschrijving)

        if self.rol_nu == Rollen.ROL_HWL:
            url = reverse('CompRayon:teams-rk', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})
        else:
            url = reverse('CompRayon:rayon-teams', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

        return HttpResponseRedirect(url)


# end of file
