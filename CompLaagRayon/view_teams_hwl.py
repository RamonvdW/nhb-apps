# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TeamType
from Competitie.definities import DEEL_RK
from Competitie.models import RegiocompetitieSporterBoog, Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Score.definities import AG_NUL
import datetime


TEMPLATE_COMPRAYON_VERTEAMS = 'complaagrayon/hwl-teams.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_WIJZIG = 'complaagrayon/hwl-teams-wijzig.dtl'
TEMPLATE_COMPRAYON_VERTEAMS_KOPPELEN = 'complaagrayon/hwl-teams-koppelen.dtl'


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
    """ gebruik AG/VSG van gekoppelde sporters om team aanvangsgemiddelde te berekenen
        en bepaal aan de hand daarvan de team wedstrijdklasse
    """

    ags = list()
    if open_inschrijving:
        for deelnemer in rk_team.tijdelijke_leden.all():
            ag, _ = bepaal_regioschutter_gemiddelde_voor_rk_teams(deelnemer)
            ags.append(ag)
        # for
    else:
        for deelnemer in rk_team.gekoppelde_leden.all():
            ags.append(deelnemer.gemiddelde)
        # for

    rk_team.team_klasse = None       # wordt later bepaald, als de teams al bevroren zijn

    if len(ags) >= 3:
        # bereken de team sterkte: de som van de 3 sterkste sporters
        ags.sort(reverse=True)
        rk_team.aanvangsgemiddelde = sum(ags[:3])
    else:
        rk_team.aanvangsgemiddelde = AG_NUL

    rk_team.save(update_fields=['aanvangsgemiddelde', 'team_klasse'])


class TeamsRkView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de rayonkampioenschappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_VERTEAMS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def _get_deelkamp_rk(self, deelkamp_pk) -> Kampioenschap:
        # haal de gevraagde kampioenschap op
        try:
            deelkamp_pk = int(deelkamp_pk[:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'rayon')
                        .get(pk=deelkamp_pk,
                             is_afgesloten=False,
                             deel=DEEL_RK,
                             rayon=self.functie_nu.vereniging.regio.rayon))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if not ('F' <= comp.fase_teams <= 'K'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase 1')

        vanaf = comp.begin_fase_F + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase 2')

        deelkamp.open_inschrijving = comp.fase_teams < 'J'       # regio vs RK fase

        deelkamp.datum_einde_knutselen_teams_rk_bk = comp.datum_klassengrenzen_rk_bk_teams

        return deelkamp

    def _get_rk_teams(self, deelkamp, is_vastgesteld):

        if deelkamp.competitie.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        if deelkamp.open_inschrijving:
            # open inschrijving RK
            rk_teams = (KampioenschapTeam
                        .objects
                        .select_related('vereniging',
                                        'team_type')
                        .filter(kampioenschap=deelkamp,
                                vereniging=self.functie_nu.vereniging)
                        .annotate(schutters_count=Count('tijdelijke_leden'))
                        .order_by('volg_nr'))

        else:
            # team deelnemers bestaat uit gerechtigde RK deelnemers
            rk_teams = (KampioenschapTeam
                        .objects
                        .select_related('vereniging',
                                        'team_type')
                        .filter(kampioenschap=deelkamp,
                                vereniging=self.functie_nu.vereniging)
                        .annotate(schutters_count=Count('gekoppelde_leden'))
                        .order_by('volg_nr'))

        for rk_team in rk_teams:
            rk_team.aantal = rk_team.schutters_count
            rk_team.ag_str = "%05.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
            rk_team.ag_str = rk_team.ag_str.replace('.', ',')

            if not is_vastgesteld:
                rk_team.url_wijzig = reverse('CompLaagRayon:teams-rk-wijzig',
                                             kwargs={'deelkamp_pk': deelkamp.pk,
                                                     'rk_team_pk': rk_team.pk})

            # koppelen == bekijken
            rk_team.url_koppelen = reverse('CompLaagRayon:teams-rk-koppelen',
                                           kwargs={'rk_team_pk': rk_team.pk})
        # for

        return rk_teams

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        context['deelkamp'] = deelkamp = self._get_deelkamp_rk(kwargs['deelkamp_pk'])

        context['rk_bk_klassen_vastgesteld'] = is_vastgesteld = deelkamp.competitie.klassengrenzen_vastgesteld_rk_bk

        context['rk_teams'] = self._get_rk_teams(deelkamp, is_vastgesteld)

        if not is_vastgesteld:
            context['url_nieuw_team'] = reverse('CompLaagRayon:teams-rk-nieuw',
                                                kwargs={'deelkamp_pk': deelkamp.pk})

        comp = deelkamp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer Vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (None, 'Teams RK'),
        )

        return context


class WijzigRKTeamsView(UserPassesTestMixin, TemplateView):

    """ laat de HWL een nieuw team aanmaken of een bestaand team wijzigen voor het RK
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_VERTEAMS_WIJZIG
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rol.ROL_HWL

    def _get_deelkamp_rk(self, deelkamp_pk) -> Kampioenschap:
        # haal de gevraagde kampioenschap op
        try:
            deelkamp_pk = int(deelkamp_pk[:6])     # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'rayon')
                        .get(pk=deelkamp_pk,
                             is_afgesloten=False,
                             deel=DEEL_RK,
                             rayon=self.functie_nu.vereniging.regio.rayon))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if not ('F' <= comp.fase_teams <= 'J'):
            # staat niet meer open voor instellen RK teams
            raise Http404('Competitie is niet in de juiste fase 1')

        vanaf = comp.begin_fase_F + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)
        if datetime.date.today() < vanaf:
            raise Http404('Competitie is niet in de juiste fase 2')

        return deelkamp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        deelkamp = self._get_deelkamp_rk(kwargs['deelkamp_pk'])
        ver = self.functie_nu.vereniging
        comp = deelkamp.competitie

        teamtype_default = None
        context['opt_team_type'] = team_typen = comp.teamtypen.order_by('volgorde')
        for team_type in team_typen:
            team_type.choice_name = team_type.afkorting
            if team_type.afkorting[0] == 'R':        # R or R2
                teamtype_default = team_type
        # for

        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .get(pk=rk_team_pk,
                            kampioenschap=deelkamp,
                            vereniging=ver))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden of niet van jouw vereniging')
        except KeyError:
            # dit is een nieuw rk_team
            rk_team = KampioenschapTeam(
                            pk=0,
                            vereniging=self.functie_nu.vereniging,
                            team_type=teamtype_default)

        context['rk_team'] = rk_team

        for obj in team_typen:
            obj.actief = rk_team.team_type == obj
        # for

        context['url_opslaan'] = reverse('CompLaagRayon:teams-rk-wijzig',
                                         kwargs={'deelkamp_pk': deelkamp.pk,
                                                 'rk_team_pk': rk_team.pk})

        if rk_team.pk > 0:
            context['url_verwijderen'] = context['url_opslaan']

        comp = deelkamp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer Vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagRayon:teams-rk', kwargs={'deelkamp_pk': deelkamp.pk}), 'Teams RK'),
            (None, 'Wijzig team')
        )

        return context

    def post(self, request, *args, **kwargs):
        deelkamp = self._get_deelkamp_rk(kwargs['deelkamp_pk'])
        comp = deelkamp.competitie
        ver = self.functie_nu.vereniging

        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])    # afkappen voor de veiligheid
        except (ValueError, KeyError):
            raise Http404('Slechte parameter')

        # default = terug naar het overzicht van de Teams RK pagina
        url = reverse('CompLaagRayon:teams-rk',
                      kwargs={'deelkamp_pk': deelkamp.pk})

        if rk_team_pk == 0:
            # nieuw rk_team
            volg_nrs = (KampioenschapTeam
                        .objects
                        .filter(kampioenschap=deelkamp,
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
                team_type = comp.teamtypen.get(afkorting=afkorting)
            except (IndexError, TeamType.DoesNotExist):
                raise Http404('Onbekend team type')

            rk_team = KampioenschapTeam(
                            kampioenschap=deelkamp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=team_type,
                            team_naam=' ')
            rk_team.save()

            verwijderen = False

            # na aanmaken meteen door naar de 'koppelen' pagina
            url = reverse('CompLaagRayon:teams-rk-koppelen',
                          kwargs={'rk_team_pk': rk_team.pk})
        else:
            try:
                rk_team = (KampioenschapTeam
                           .objects
                           .select_related('team_type')
                           .get(pk=rk_team_pk,
                                kampioenschap=deelkamp))
            except KampioenschapTeam.DoesNotExist:
                raise Http404('Team bestaat niet')

            if rk_team.vereniging != self.functie_nu.vereniging:
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
                    rk_team.team_klasse = None
                    rk_team.save()

                    # verwijder eventueel gekoppelde sporters bij wijziging rk_team type,
                    # om verkeerde boog typen te voorkomen
                    rk_team.tijdelijke_leden.clear()
                    rk_team.gekoppelde_leden.clear()
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
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.readonly = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_RKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het rk_team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('kampioenschap',
                                       'kampioenschap__competitie',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            ver = self.functie_nu.vereniging
            if rk_team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = rk_team.vereniging

        context['rk_team'] = rk_team

        deelkamp = rk_team.kampioenschap

        comp = deelkamp.competitie
        comp.bepaal_fase()

        context['alleen_bekijken'] = alleen_bekijken = (comp.fase_teams > 'J')

        if not ('F' <= comp.fase_teams <= 'L'):
            raise Http404('Competitie is niet in de juiste fase')

        boog_typen = rk_team.team_type.boog_typen.all()
        boog_pks = boog_typen.values_list('pk', flat=True)
        context['boog_typen'] = boog_typen

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25
        ag_str = "%05.1f" % (rk_team.aanvangsgemiddelde * aantal_pijlen)
        rk_team.ag_str = ag_str.replace('.', ',')

        if comp.fase_teams <= 'G':
            # alle leden van de vereniging die meedoen aan de regiocompetitie mogen gekozen worden

            context['onder_voorbehoud'] = True

            pks = rk_team.tijdelijke_leden.values_list('pk', flat=True)

            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('tijdelijke_leden')
                         .values_list('tijdelijke_leden__pk', flat=True))

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__competitie=comp,
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
            pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)

            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(kampioenschap=deelkamp,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('gekoppelde_leden')
                         .values_list('gekoppelde_leden__pk', flat=True))

            deelnemers = (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=deelkamp,
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
            context['url_opslaan'] = reverse('CompLaagRayon:teams-rk-koppelen',
                                             kwargs={'rk_team_pk': rk_team.pk})

        comp = deelkamp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (url_overzicht, 'Beheer Vereniging'),
                (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:teams-rk', kwargs={'deelkamp_pk': deelkamp.pk}), 'Teams RK'),
                (None, 'Koppel teamleden'))
        else:
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:rayon-teams', kwargs={'deelkamp_pk': deelkamp.pk}), 'RK teams'),
                (None, 'Koppel teamleden'))

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL op Opslaan drukt om team leden te koppelen """

        # zoek het team erbij en controleer dat deze bij de vereniging van de beheerder hoort
        try:
            rk_team_pk = int(kwargs['rk_team_pk'][:6])      # afkappen voor de veiligheid
            rk_team = (KampioenschapTeam
                       .objects
                       .select_related('kampioenschap',
                                       'team_type')
                       .prefetch_related('team_type__boog_typen')
                       .get(pk=rk_team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Team niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            ver = self.functie_nu.vereniging
            if rk_team.vereniging != ver:
                raise Http404('Team is niet van jouw vereniging')
        else:
            ver = rk_team.vereniging

        deelkamp = rk_team.kampioenschap

        comp = deelkamp.competitie
        comp.bepaal_fase()
        if not ('E' <= comp.fase_teams <= 'J'):
            raise Http404('Competitie is niet in de juiste fase')

        open_inschrijving = comp.fase_teams <= 'G'        # regio vs RK fase

        # toegestane boogtypen en schutters
        boog_pks = rk_team.team_type.boog_typen.values_list('pk', flat=True)

        if open_inschrijving:
            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(kampioenschap=deelkamp,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('tijdelijke_leden')
                         .values_list('tijdelijke_leden__pk', flat=True))

            ok_pks = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie__competitie=comp,
                              bij_vereniging=ver,
                              sporterboog__boogtype__in=boog_pks)
                      .values_list('pk', flat=True))

        else:
            bezet_pks = (KampioenschapTeam
                         .objects
                         .filter(kampioenschap=deelkamp,
                                 vereniging=ver)
                         .exclude(pk=rk_team_pk)
                         .prefetch_related('gekoppelde_leden')
                         .values_list('gekoppelde_leden__pk', flat=True))

            ok_pks = (KampioenschapSporterBoog
                      .objects
                      .filter(kampioenschap=deelkamp,
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
            rk_team.tijdelijke_leden.clear()
            rk_team.tijdelijke_leden.add(*pks)
        else:
            rk_team.gekoppelde_leden.clear()
            rk_team.gekoppelde_leden.add(*pks)

        bepaal_rk_team_tijdelijke_sterkte_en_klasse(rk_team, open_inschrijving)

        if self.rol_nu == Rol.ROL_HWL:
            url = reverse('CompLaagRayon:teams-rk', kwargs={'deelkamp_pk': deelkamp.pk})
        else:
            url = reverse('CompLaagRayon:rayon-teams', kwargs={'deelkamp_pk': deelkamp.pk})

        return HttpResponseRedirect(url)


# end of file
