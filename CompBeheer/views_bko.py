# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_RK, MUTATIE_DOORZETTEN_REGIO_NAAR_RK, MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK
from Competitie.models import (Competitie, Regiocompetitie, CompetitieMutatie, Kampioenschap,
                               CompetitieTeamKlasse, KampioenschapTeam)
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics

TEMPLATE_COMPBEHEER_DOORZETTEN_REGIO_NAAR_RK = 'compbeheer/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_INDIV_RK_NAAR_BK = 'compbeheer/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPBEHEER_DOORZETTEN_TEAMS_RK_NAAR_BK = 'compbeheer/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_INDIV = 'compbeheer/bko-doorzetten-voorbij-bk.dtl'
TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_TEAMS = 'compbeheer/bko-doorzetten-voorbij-bk.dtl'
TEMPLATE_COMPBEHEER_KLASSENGRENZEN_TEAMS_VASTSTELLEN = 'compbeheer/bko-klassengrenzen-vaststellen-rk-bk-teams.dtl'


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
        return self.rol_nu == Rollen.ROL_BKO

    @staticmethod
    def _get_regio_status(competitie):
        # sporters komen uit de 4 regio's van het rayon
        regio_deelcomps = (Regiocompetitie
                           .objects
                           .filter(competitie=competitie)
                           .select_related('nhb_regio',
                                           'nhb_regio__rayon')
                           .order_by('nhb_regio__regio_nr'))

        for obj in regio_deelcomps:
            obj.regio_str = str(obj.nhb_regio.regio_nr)
            obj.rayon_str = str(obj.nhb_regio.rayon.rayon_nr)

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
        if comp.fase_indiv < 'E' or comp.fase_indiv >= 'J':
            # kaartjes werd niet getoond, dus je zou hier niet moeten zijn
            raise Http404('Verkeerde competitie fase')

        context['comp'] = comp
        context['regio_status'] = self._get_regio_status(comp)

        if comp.fase_indiv == 'G':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('CompBeheer:bko-doorzetten-regio-naar-rk',
                                                kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
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
        account = self.request.user
        door_str = "BKO %s" % account.volledige_naam()

        CompetitieMutatie(mutatie=MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                          door=door_str,
                          competitie=comp).save()

        return HttpResponseRedirect(reverse('Competitie:kies'))


class DoorzettenIndivRKNaarBKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de BK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_INDIV_RK_NAAR_BK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

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

        context['comp'] = comp

        comp.bepaal_fase()
        if comp.fase_indiv != 'L':
            raise Http404('Verkeerde competitie fase')

        # bepaal de status van elk rayon

        status2str = {True: 'Afgesloten', False: 'Actief'}

        context['rk_status'] = deelkamps = (Kampioenschap
                                            .objects
                                            .select_related('nhb_rayon')
                                            .filter(competitie=comp,
                                                    deel=DEEL_RK)
                                            .order_by('nhb_rayon__rayon_nr'))
        klaar = True
        for deelkamp in deelkamps:
            deelkamp.rayon_str = 'Rayon %s' % deelkamp.nhb_rayon.rayon_nr
            deelkamp.status_str = status2str[deelkamp.is_afgesloten]
            deelkamp.indiv_str = status2str[deelkamp.is_klaar_indiv]
            if not deelkamp.is_klaar_indiv:
                klaar = False
        # for

        if klaar:
            context['url_doorzetten'] = reverse('CompBeheer:bko-rk-indiv-doorzetten-naar-bk',
                                                kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Competitie doorzetten')
        )

        menu_dynamics(self.request, context)
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Doorzetten naar de volgende fase' gebruikt wordt
            door de BKO, om de competitie door te zetten van de RK naar de BK fase.
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
        if comp.fase_indiv != 'L':
            raise Http404('Verkeerde competitie fase')

        # vraag de achtergrond taak alle stappen van het afsluiten uit te voeren
        # dit voorkomt ook race conditions / dubbel uitvoeren
        account = request.user
        door_str = "BKO %s" % account.volledige_naam()

        CompetitieMutatie(mutatie=MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK,
                          door=door_str,
                          competitie=comp).save()

        return HttpResponseRedirect(reverse('Competitie:kies'))


class DoorzettenTeamsRKNaarBKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de BK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DOORZETTEN_TEAMS_RK_NAAR_BK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

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

        comp.bepaal_fase()
        if comp.fase_teams != 'L':
            raise Http404('Verkeerde competitie fase')

        # klaar om door te zetten
        context['url_doorzetten'] = reverse('CompBeheer:bko-rk-teams-doorzetten-naar-bk',
                                                kwargs={'comp_pk': comp.pk})

        # bepaal de status van elk rayon
        status2str = {True: 'Afgesloten', False: 'Actief'}

        context['rk_status'] = deelkamps = (Kampioenschap
                                            .objects
                                            .select_related('nhb_rayon')
                                            .filter(competitie=comp,
                                                    deel=DEEL_RK)
                                            .order_by('nhb_rayon__rayon_nr'))
        for deelkamp in deelkamps:
            deelkamp.rayon_str = 'Rayon %s' % deelkamp.nhb_rayon.rayon_nr
            deelkamp.status_str = status2str[deelkamp.is_afgesloten]
            deelkamp.indiv_str = status2str[deelkamp.is_klaar_indiv]
            deelkamp.team_str = status2str[deelkamp.is_klaar_teams]
        # for

        context['comp'] = comp

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Competitie doorzetten')
        )

        menu_dynamics(self.request, context)
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Doorzetten naar de volgende fase' gebruikt wordt
            door de BKO, om de competitie door te zetten van de RK naar de BK fase.
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
        if comp.fase_teams != 'L':
            raise Http404('Verkeerde competitie fase')

        # vraag de achtergrond taak alle stappen van het afsluiten uit te voeren
        # dit voorkomt ook race conditions / dubbel uitvoeren
        account = request.user
        door_str = "BKO %s" % account.volledige_naam()

        CompetitieMutatie(mutatie=MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK,
                          door=door_str,
                          competitie=comp).save()

        return HttpResponseRedirect(reverse('Competitie:kies'))


class BevestigEindstandBKIndivView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de BK wedstrijden afsluiten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_INDIV
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rollen.ROL_BKO

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

        # correcte beheerder?
        if comp.afstand != self.functie_nu.comp_type:
            raise PermissionDenied('Niet de beheerder')

        comp.bepaal_fase()
        if comp.fase_indiv != 'P':          # TODO: implementatie voor teams
            raise Http404('Verkeerde competitie fase')

        context['url_doorzetten'] = reverse('CompBeheer:bko-bevestig-eindstand-bk-indiv',
                                            kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'BK afsluiten' gebruikt wordt door de BKO.
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
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
        if comp.fase_indiv != 'P':
            raise Http404('Verkeerde competitie fase')

        comp.bk_indiv_afgesloten = True     # TODO: ondersteuning teams
        comp.save(update_fields=['bk_indiv_afgesloten'])

        return HttpResponseRedirect(reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}))


class BevestigEindstandBKTeamsView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de BK teams afsluiten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_BEVESTIG_EINDSTAND_BK_INDIV
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rollen.ROL_BKO

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

        # correcte beheerder?
        if comp.afstand != self.functie_nu.comp_type:
            raise PermissionDenied('Niet de beheerder')

        comp.bepaal_fase()
        if comp.fase_indiv != 'P':          # TODO: implementatie voor teams
            raise Http404('Verkeerde competitie fase')

        context['url_doorzetten'] = reverse('CompBeheer:bko-bevestig-eindstand-bk-teams',
                                            kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'BK afsluiten' gebruikt wordt door de BKO.
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
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
        if comp.fase_indiv != 'P':
            raise Http404('Verkeerde competitie fase')

        comp.bk_indiv_afgesloten = True     # TODO: ondersteuning teams
        comp.save(update_fields=['bk_indiv_afgesloten'])

        return HttpResponseRedirect(reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}))


class KlassengrenzenTeamsVaststellenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de teams klassengrenzen voor het RK en BK vaststellen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_KLASSENGRENZEN_TEAMS_VASTSTELLEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

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

        if comp.afstand == '18':
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
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
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
                            break       # from the for
                    # for

            team.save(update_fields=['team_klasse'])
        # for

        # zet de competitie door naar fase K
        comp.klassengrenzen_vastgesteld_rk_bk = True
        comp.save(update_fields=['klassengrenzen_vastgesteld_rk_bk'])

        url = reverse('CompBeheer:overzicht',
                      kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)


# end of file
