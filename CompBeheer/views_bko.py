# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import (MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KAMP_INDIV_AFSLUITEN, MUTATIE_KAMP_TEAMS_AFSLUITEN)
from Competitie.models import Competitie, CompetitieTeamKlasse, Regiocompetitie, KampioenschapTeam, CompetitieMutatie
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Site.core.background_sync import BackgroundSync

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)

TEMPLATE_COMPBEHEER_DOORZETTEN_REGIO_NAAR_RK = 'compbeheer/bko-doorzetten-1a-regio-naar-rk.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_KLASSENGRENZEN_KAMP_TEAMS = 'compbeheer/bko-doorzetten-1b-klassengrenzen-rk-bk-teams.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_RK_NAAR_BK_INDIV = 'compbeheer/bko-doorzetten-2a-rk-naar-bk-indiv.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_RK_NAAR_BK_TEAMS = 'compbeheer/bko-doorzetten-2b-rk-naar-bk-teams.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_BK_KLEINE_KLASSEN_INDIV = 'compbeheer/bko-doorzetten-3a-bk-kleine-klassen-indiv.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_BK_KLEINE_KLASSEN_TEAMS = 'compbeheer/bko-doorzetten-3b-bk-kleine-klassen-teams.dtl'
TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_INDIV = 'compbeheer/bko-doorzetten-4a-bevestig-eindstand-bk-indiv.dtl'
TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_TEAMS = 'compbeheer/bko-doorzetten-4b-bevestig-eindstand-bk-teams.dtl'


class DoorzettenRegioNaarRKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de RK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_REGIO_NAAR_RK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    @staticmethod
    def _get_regio_status(competitie):
        # sporters komen uit de 4 regio's van het rayon
        regio_deelcomps = (Regiocompetitie
                           .objects
                           .filter(competitie=competitie)
                           .select_related('regio')
                           .order_by('regio__regio_nr'))

        for obj in regio_deelcomps:
            obj.regio_str = str(obj.regio.regio_nr)
            obj.rayon_str = str(obj.regio.rayon_nr)

            if obj.is_afgesloten:
                obj.status_str = "Afgesloten"
                obj.status_groen = True
            else:
                # nog actief
                obj.status_str = "Actief"
                if obj.regio_organiseert_teamcompetitie:
                    # check hoever deze regio is met de teamcompetitie rondes
                    if obj.huidige_team_ronde <= 7:
                        obj.status_str += ' (team ronde %s)' % obj.huidige_team_ronde
                    elif obj.huidige_team_ronde == 99:
                        obj.status_str += ' / Teams klaar'
        # for

        return regio_deelcomps

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if comp.afstand != self.functie_nu.comp_type:
            raise Http404('Verkeerde competitie')

        comp.bepaal_fase()
        if comp.fase_indiv < 'F' or comp.fase_indiv >= 'J':
            # kaartje werd niet getoond, dus je zou hier niet moeten zijn
            raise Http404('Verkeerde competitie fase')

        context['comp'] = comp
        context['regio_status'] = self._get_regio_status(comp)

        if comp.fase_indiv == 'G':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('CompBeheer:bko-doorzetten-regio-naar-rk',
                                                kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Doorzetten' gebruikt wordt
            om de competitie door te zetten naar de RK fase
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if comp.fase_indiv != 'G':
            raise Http404('Verkeerde competitie fase')

        # fase G garandeert dat alle regiocompetities afgesloten zijn

        # vraag de achtergrond taak alle stappen van het afsluiten uit te voeren
        # dit voorkomt ook race conditions / dubbel uitvoeren
        account = get_account(self.request)
        door_str = "BKO %s" % account.volledige_naam()
        door_str = door_str[:149]

        CompetitieMutatie(mutatie=MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                          door=door_str,
                          competitie=comp).save()

        mutatie_ping.ping()

        # we wachten niet tot deze verwerkt is

        return HttpResponseRedirect(reverse('Competitie:kies'))


class KlassengrenzenVaststellenRkBkTeamsView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de teams klassengrenzen voor het RK en BK vaststellen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_KLASSENGRENZEN_KAMP_TEAMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    @staticmethod
    def _tel_rk_teams(comp):
        """ Verdeel de ingeschreven (en complete) teams van elk team type over de beschikbare
            team wedstrijdklassen, door de grenzen tussen de klassen te bepalen.
        """

        teamtype_pks = list()
        teamtypes = list()

        teamtype2wkl = dict()       # [team_type.pk] = list(CompetitieTeamKlasse)
        for rk_wkl in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .select_related('team_type')
                       .order_by('volgorde')):

            teamtype_pk = rk_wkl.team_type.pk
            if teamtype_pk not in teamtype_pks:
                teamtypes.append(rk_wkl.team_type)
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

        niet_compleet_team = False

        for rk_team in (KampioenschapTeam
                        .objects
                        .filter(kampioenschap__competitie=comp)
                        .select_related('team_type')
                        .annotate(sporter_count=Count('tijdelijke_leden'))
                        .order_by('team_type__volgorde',
                                  '-aanvangsgemiddelde')):

            if rk_team.aanvangsgemiddelde < 0.001:
                niet_compleet_team = True
            else:
                team_type_pk = rk_team.team_type.pk
                try:
                    teamtype2sterktes[team_type_pk].append(rk_team.aanvangsgemiddelde)
                except KeyError:
                    # abnormal: unexpected team type used in RK team
                    pass
        # for

        return teamtypes, teamtype2wkl, teamtype2sterktes, niet_compleet_team

    def _bepaal_klassengrenzen(self, comp):
        tts, tt2wkl, tt2sterktes, niet_compleet_team = self._tel_rk_teams(comp)

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        grenzen = list()

        if not niet_compleet_team:
            for tt in tts:
                klassen = tt2wkl[tt.pk]
                sterktes = tt2sterktes[tt.pk]
                count = len(sterktes)
                index = 0

                aantal_klassen = len(klassen)
                aantal_per_klasse = count / aantal_klassen

                ophoog_factor = 0.4
                ophoog_step = 1.0 / aantal_klassen     # 5 klassen --> 0.2 --> +0.4 +0.2 +0.0 -0.2

                klassen_lijst = list()
                for klasse in klassen:
                    min_ag = 0.0

                    if len(klassen_lijst) + 1 == aantal_klassen:
                        # laatste klasse = geen ondergrens
                        step = count - index
                        min_ag_str = ""     # toon n.v.t.
                    else:
                        step = round(aantal_per_klasse + ophoog_factor)
                        index += step
                        ophoog_factor -= ophoog_step
                        if index <= count and count > 0:
                            min_ag = sterktes[index - 1]

                        min_ag_str = "%05.1f" % (min_ag * aantal_pijlen)
                        min_ag_str = min_ag_str.replace('.', ',')

                    tup = (klasse.beschrijving, step, min_ag, min_ag_str)
                    klassen_lijst.append(tup)
                # for

                tup = (len(klassen) + 1, tt.beschrijving, count, klassen_lijst)
                grenzen.append(tup)
            # for

        return grenzen, niet_compleet_team

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

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        if comp.fase_teams != 'J':
            raise Http404('Competitie niet in de juiste fase')

        context['grenzen'], context['niet_compleet_team'] = self._bepaal_klassengrenzen(comp)

        if context['niet_compleet_team']:
            context['url_terug'] = reverse('CompBeheer:overzicht',
                                           kwargs={'comp_pk': comp.pk})

        context['url_vaststellen'] = reverse('CompBeheer:klassengrenzen-vaststellen-rk-bk-teams',
                                             kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

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

        if comp.klassengrenzen_vastgesteld_rk_bk:
            raise Http404('De klassengrenzen zijn al vastgesteld')

        if comp.fase_teams != 'J':
            raise Http404('Competitie niet in de juiste fase')

        # vul de klassengrenzen in voor RK/BK  teams

        grenzen, niet_compleet_team = self._bepaal_klassengrenzen(comp)

        if niet_compleet_team:
            raise Http404('Niet alle teams zijn compleet')

        beschrijving2team_klasse = dict()

        for team_klasse in (CompetitieTeamKlasse
                            .objects
                            .filter(is_voor_teams_rk_bk=True,
                                    competitie=comp)
                            .select_related('team_type')):
            beschrijving2team_klasse[team_klasse.beschrijving] = team_klasse
        # for

        teamtype_pk2klassen = dict()        # hoogste klasse eerst

        # neem de voorgestelde klassengrenzen over
        for _, _, _, klassen_lijst in grenzen:
            for beschrijving, _, min_ag, _ in klassen_lijst:
                try:
                    team_klasse = beschrijving2team_klasse[beschrijving]
                except KeyError:
                    raise Http404('Kan competitie klasse %s niet vinden' % repr(beschrijving))

                team_klasse.min_ag = min_ag
                team_klasse.save(update_fields=['min_ag'])

                teamtype_pk = team_klasse.team_type.pk
                try:
                    teamtype_pk2klassen[teamtype_pk].append(team_klasse)
                except KeyError:
                    teamtype_pk2klassen[teamtype_pk] = [team_klasse]
            # for
        # for

        # plaats elk RK team in een wedstrijdklasse
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap__competitie=comp)
                     .annotate(sporter_count=Count('gekoppelde_leden'))):

            team.team_klasse = None
            if 3 <= team.sporter_count <= 4:
                # dit is een volledig team
                try:
                    klassen = teamtype_pk2klassen[team.team_type.pk]
                except KeyError:
                    # onverwacht team type (ignore, avoid crash)
                    pass
                else:
                    for team_klasse in klassen:
                        if team.aanvangsgemiddelde >= team_klasse.min_ag:
                            team.team_klasse = team_klasse
                            team.team_klasse_volgende_ronde = team_klasse
                            break       # from the for
                    # for

            team.save(update_fields=['team_klasse', 'team_klasse_volgende_ronde'])
        # for

        # zet de competitie door naar fase K
        comp.klassengrenzen_vastgesteld_rk_bk = True
        comp.save(update_fields=['klassengrenzen_vastgesteld_rk_bk'])

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)


class DoorzettenBasisView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO een "doorzetten" actie in gang zetten """

    # class variables shared by all instances
    template_name = None
    expected_fase = '?'
    check_indiv_fase = True
    url_name = None             # naar POST handler, voor doorzetten
    mutatie_code = None

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BKO

    def _check_competitie_fase(self, comp_pk_str):
        try:
            comp_pk = int(comp_pk_str[:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # correcte beheerder?
        if comp.afstand != self.functie_nu.comp_type:
            raise PermissionDenied('Niet de beheerder')

        comp.bepaal_fase()

        if self.check_indiv_fase:
            check_fase = comp.fase_indiv
        else:
            check_fase = comp.fase_teams

        if check_fase != self.expected_fase:
            raise Http404('Verkeerde competitie fase')

        return comp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp = self._check_competitie_fase(kwargs['comp_pk'])
        context['comp'] = comp

        context['url_doorzetten'] = reverse('CompBeheer:%s' % self.url_name,
                                            kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Competitie doorzetten')
        )

        return context

    def doorzetten(self, door_account, comp):
        # vraag de achtergrond taak alle stappen van het afsluiten uit te voeren
        # dit voorkomt ook race conditions / dubbel uitvoeren
        door_str = "BKO %s" % door_account.volledige_naam()
        door_str = door_str[:149]

        CompetitieMutatie(mutatie=self.mutatie_code,
                          door=door_str,
                          competitie=comp).save()

        mutatie_ping.ping()

        # we wachten niet tot deze verwerkt is
        # noteer: hierdoor geeft de test ook geen dekking voor de achtergrondtaak

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de BKO de knop 'Doorzetten naar de volgende fase' gebruikt """

        comp = self._check_competitie_fase(kwargs['comp_pk'])

        door_account = get_account(request)
        self.doorzetten(door_account, comp)

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        return HttpResponseRedirect(url)


class DoorzettenIndivRKNaarBKView(DoorzettenBasisView):

    """ Met deze view kan de BKO de individuele competitie doorzetten naar de BK fase """

    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_RK_NAAR_BK_INDIV
    expected_fase = 'L'
    check_indiv_fase = True
    url_name = 'bko-rk-indiv-doorzetten-naar-bk'
    mutatie_code = MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK


class DoorzettenTeamsRKNaarBKView(DoorzettenBasisView):

    """ Met deze view kan de BKO de teamcompetitie doorzetten naar de BK fase """

    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_RK_NAAR_BK_TEAMS
    expected_fase = 'L'
    check_indiv_fase = False
    url_name = 'bko-rk-teams-doorzetten-naar-bk'
    mutatie_code = MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK


class KleineBKKlassenZijnSamengevoegdIndivView(DoorzettenBasisView):

    """ Met deze view kan de BKO bevestigen dat kleine individuele BK klassen samengevoegd zijn """

    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_BK_KLEINE_KLASSEN_INDIV
    expected_fase = 'N'
    check_indiv_fase = True
    url_name = 'bko-bk-indiv-kleine-klassen'

    def doorzetten(self, account, comp):
        comp.bk_indiv_klassen_zijn_samengevoegd = True
        comp.save(update_fields=['bk_indiv_klassen_zijn_samengevoegd'])


class KleineBKKlassenZijnSamengevoegdTeamsView(DoorzettenBasisView):

    """ Met deze view kan de BKO bevestigen dat kleine BK teams klassen samengevoegd zijn """

    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_BK_KLEINE_KLASSEN_TEAMS
    expected_fase = 'N'
    check_indiv_fase = False
    url_name = 'bko-bk-teams-kleine-klassen'

    def doorzetten(self, account, comp):
        comp.bk_teams_klassen_zijn_samengevoegd = True
        comp.save(update_fields=['bk_teams_klassen_zijn_samengevoegd'])


class BevestigEindstandBKIndivView(DoorzettenBasisView):

    """ Met deze view kan de BKO de eindstand van de BK individueel bevestigen """

    template_name = TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_INDIV
    expected_fase = 'P'
    check_indiv_fase = True
    url_name = 'bko-bevestig-eindstand-bk-indiv'
    mutatie_code = MUTATIE_KAMP_INDIV_AFSLUITEN


class BevestigEindstandBKTeamsView(DoorzettenBasisView):

    """ Met deze view kan de BKO de eindstand van de BK teams bevestigen """

    template_name = TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_TEAMS
    expected_fase = 'P'
    check_indiv_fase = False
    url_name = 'bko-bevestig-eindstand-bk-teams'
    mutatie_code = MUTATIE_KAMP_TEAMS_AFSLUITEN


# end of file
