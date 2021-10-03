# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.models import (CompetitieKlasse, AG_NUL, DeelCompetitie, LAAG_RK,
                               RegioCompetitieSchutterBoog, KampioenschapTeam)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
import datetime


TEMPLATE_COMPRAYON_VERTEAMS = 'comprayon/ver-teams.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_WIJZIG = 'comprayon/ver-teams-wijzig.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_KOPPELEN = 'comprayon/ver-teams-koppelen.dtl'


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


def bepaal_rk_team_tijdelijke_sterkte_en_klasse(comp, rk_team):
    """ gebruik AG/VSG van gekoppelde schutters om team aanvangsgemiddelde te berekenen
        en bepaal aan de hand daarvan de team wedstrijdklasse
    """

    ags = list()
    for deelnemer in rk_team.tijdelijke_schutters.all():
        ag, _ = bepaal_regioschutter_gemiddelde_voor_rk_teams(deelnemer)
        ags.append(ag)
    # for

    rk_team.klasse = None

    if len(ags) >= 3:
        # bereken de team sterkte: de som van de 3 sterkste sporters
        ags.sort(reverse=True)
        ag = sum(ags[:3])

        # bepaal de wedstrijdklasse
        for klasse in (CompetitieKlasse
                       .objects
                       .filter(competitie=comp,
                               team__team_type=rk_team.team_type)
                       .order_by('min_ag', '-team__volgorde')):  # oplopend AG (=hogere klasse later)
            if ag >= klasse.min_ag:
                rk_team.klasse = klasse
        # for
    else:
        ag = AG_NUL

    rk_team.aanvangsgemiddelde = ag
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

        return deelcomp

    def _get_rk_teams(self, deelcomp_rk):

        if deelcomp_rk.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        rk_teams = (KampioenschapTeam
                    .objects
                    .select_related('vereniging',
                                    'team_type')
                    .filter(deelcompetitie=deelcomp_rk,
                            vereniging=self.functie_nu.nhb_ver)
                    .annotate(tijdelijke_schutters_count=Count('tijdelijke_schutters'))
                    .order_by('volg_nr'))

        for rk_team in rk_teams:
            rk_team.aantal = rk_team.tijdelijke_schutters_count
            rk_team.ag_str = "%05.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
            rk_team.ag_str = rk_team.ag_str.replace('.', ',')

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

        context['rk_teams'] = self._get_rk_teams(deelcomp_rk)

        context['url_nieuw_team'] = reverse('CompRayon:teams-rk-nieuw',
                                            kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

        menu_dynamics(self.request, context, actief='vereniging')
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
        context['deelcomp_rk'] = deelcomp_rk = self._get_deelcomp_rk(kwargs['rk_deelcomp_pk'])
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
            rk_team_pk = int(kwargs['rk_team_pk'][:6])
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

        for obj in teams:
            obj.actief = rk_team.team_type == obj
        # for

        context['url_opslaan'] = reverse('CompRayon:teams-rk-wijzig',
                                         kwargs={'rk_deelcomp_pk': deelcomp_rk.pk,
                                                 'rk_team_pk': rk_team.pk})

        if rk_team.pk > 0:
            context['url_verwijderen'] = context['url_opslaan']

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        deelcomp = self._get_deelcomp_rk(kwargs['rk_deelcomp_pk'])

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
                team_type = TeamType.objects.get(afkorting=afkorting)
            except TeamType.DoesNotExist:
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
    """ Via deze view kan de HWL leden van zijn vereniging koppelen aan een team """

    template_name = TEMPLATE_COMPRAYON_VERTEAMS_KOPPELEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het rk_team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('deelcompetitie',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        ver = self.functie_nu.nhb_ver
        if rk_team.vereniging != ver:
            raise Http404('Team is niet van jouw vereniging')

        context['rk_team'] = rk_team

        context['deelcomp_rk'] = deelcomp_rk = rk_team.deelcompetitie

        comp = deelcomp_rk.competitie
        #comp.bepaal_fase()
        # TODO: vanaf wanneer wijzigingen blokkeren?

        boog_typen = rk_team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        if deelcomp_rk.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        ag_str = "%5.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
        rk_team.ag_str = ag_str.replace('.', ',')

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
                      .exclude(klasse__indiv__is_aspirant_klasse=True)            # geen aspiranten
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
        context['deelnemers'] = deelnemers

        context['url_opslaan'] = reverse('CompRayon:teams-rk-koppelen',
                                         kwargs={'rk_team_pk': rk_team.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('deelcompetitie',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        ver = self.functie_nu.nhb_ver
        if rk_team.vereniging != ver:
            raise Http404('Team is niet van jouw vereniging')

        rk_deelcomp = rk_team.deelcompetitie

        comp = rk_deelcomp.competitie
        #comp.bepaal_fase()
        # TODO: vanaf wanneer wijzigingen blokkeren?

        # toegestane boogtypen en schutters
        boog_pks = rk_team.team_type.boog_typen.values_list('pk', flat=True)

        bezet_pks = (KampioenschapTeam
                     .objects
                     .filter(vereniging=ver)
                     .exclude(pk=rk_team_pk)
                     .prefetch_related('tijdelijke_schutters')
                     .values_list('tijdelijke_schutters__pk', flat=True))

        ok_pks = (RegioCompetitieSchutterBoog
                  .objects
                  .filter(deelcompetitie__competitie=comp,
                          bij_vereniging=ver,
                          sporterboog__boogtype__in=boog_pks)
                  .values_list('pk', flat=True))

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

        rk_team.tijdelijke_schutters.clear()
        rk_team.tijdelijke_schutters.add(*pks)

        bepaal_rk_team_tijdelijke_sterkte_en_klasse(comp, rk_team)

        url = reverse('CompRayon:teams-rk', kwargs={'rk_deelcomp_pk': rk_deelcomp.pk})
        return HttpResponseRedirect(url)


# end of file
