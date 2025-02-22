# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import ORGANISATIE_WA
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_BK, DEELNAME_JA, DEELNAME_NEE, MUTATIE_KAMP_TEAMS_NUMMEREN
from Competitie.models import Kampioenschap, KampioenschapTeam, CompetitieMutatie
from Functie.definities import Rol, rol2url
from Functie.rol import rol_get_huidige_functie
from Overig.background_sync import BackgroundSync
import time

TEMPLATE_COMPBOND_BK_TEAMS = 'complaagbond/bk-teams.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class LijstBkTeamsView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BK teams en geeft de mogelijkheid om de deelname status aan te passen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_BK_TEAMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')

        context['deelkamp'] = deelkamp

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if comp.fase_teams not in ('N', 'O', 'P'):
            raise Http404('Verkeerde competitie fase')

        if comp.fase_teams != 'P':
            context['url_wijzig'] = reverse('CompLaagBond:bk-teams-wijzig-status')

        klasse2kort = list()        # [(prefix, replacement), ..]
        for boogtype in BoogType.objects.filter(organisatie=ORGANISATIE_WA):
            # ("Recurve klasse", "R")
            tup = ("%s klasse" % boogtype.beschrijving, boogtype.afkorting)
            klasse2kort.append(tup)
        # for
        kort_cache = dict()         # ["klasse beschrijving"] = "korte beschrijving"

        aantal_onbekend = 0
        aantal_aangemeld = 0
        aantal_afgemeld = 0

        teams = (KampioenschapTeam
                 .objects
                 .select_related('kampioenschap',
                                 'team_klasse',
                                 'vereniging')
                 .filter(kampioenschap=deelkamp)
                 .order_by('team_klasse__volgorde',    # groepeer per klasse
                           'volgorde'))

        for team in teams:
            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = team.vereniging.ver_nr_en_naam()
            team.klasse_str = team.team_klasse.beschrijving
            try:
                team.klasse_kort = kort_cache[team.klasse_str]
            except KeyError:
                for prefix, afkorting in klasse2kort:           # pragma: no branch
                    # prefix = "Recurve klasse"
                    if team.klasse_str.startswith(prefix):      # pragma: no branch
                        # verwijder de prefix
                        team.klasse_kort = afkorting + team.klasse_str[len(prefix):]
                        kort_cache[team.klasse_str] = team.klasse_kort
                        break
                # for

            if team.deelname == DEELNAME_NEE:
                team.status_str = 'Afgemeld'
                aantal_afgemeld += 1

            elif team.deelname == DEELNAME_JA:
                team.status_str = 'Aangemeld'
                aantal_aangemeld += 1

            else:
                team.status_str = 'Onbekend'
                aantal_onbekend += 1

            if team.is_reserve:
                team.status_str += ', Reserve'

            if comp.fase_teams != 'P':
                team.url_wijzig = reverse('CompLaagBond:bk-teams-wijzig-status')

                team.wijzig_afmelden = (team.deelname != DEELNAME_NEE)
                team.wijzig_beschikbaar = (team.deelname != DEELNAME_JA)

                if team.is_reserve:
                    team.wijzig_deelnemer = True
                else:
                    team.wijzig_toch_ja = (team.deelname == DEELNAME_NEE)
                    team.wijzig_beschikbaar = False
        # for

        context['teams'] = teams
        context['aantal_aangemeld'] = aantal_aangemeld
        context['aantal_afgemeld'] = aantal_afgemeld
        context['aantal_onbekend'] = aantal_onbekend

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'BK teams')
        )

        return context


class WijzigStatusBkTeamView(UserPassesTestMixin, View):

    """ Deze view laat de BKO de status van een BK team aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruiker op de knop OPSLAAN druk """

        team_pk = str(request.POST.get('team_pk'))[:6]      # afkappen voor de veiligheid
        status = str(request.POST.get('status'))[:15]       # afkappen voor de veiligheid

        try:
            team_pk = int(team_pk)
            team = (KampioenschapTeam
                    .objects
                    .select_related('kampioenschap',
                                    'kampioenschap__competitie')
                    .get(pk=team_pk))
        except (ValueError, KampioenschapTeam.DoesNotExist):
            raise Http404('Kan team niet vinden')

        # print(status, team)

        comp = team.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_teams not in ('N', 'O'):
            raise Http404('Mag niet meer wijzigen')

        if self.functie_nu != team.kampioenschap.functie:
            raise PermissionDenied('Niet de beheerder')

        opnieuw_nummeren = False

        if status in ("beschikbaar", "toch_ja"):
            # toch_ja is voor eerder afgemelde deelnemers
            # beschikbaar is voor reserve teams
            team.deelname = DEELNAME_JA
            team.save(update_fields=['deelname'])
            opnieuw_nummeren = True

        elif status == "afmelden":
            team.deelname = DEELNAME_NEE
            team.save(update_fields=['deelname'])
            opnieuw_nummeren = True

        elif status == "maak_deelnemer":
            # roep het reserve-team op
            team.is_reserve = False
            team.save(update_fields=['is_reserve'])
            opnieuw_nummeren = True

        if opnieuw_nummeren:
            account = get_account(request)
            door_str = "%s %s" % (rol2url[self.rol_nu], account.volledige_naam())

            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_TEAMS_NUMMEREN,
                                        door=door_str,
                                        competitie=comp,
                                        kampioenschap=team.kampioenschap,
                                        team_klasse=team.team_klasse)
            mutatie.save()
            mutatie_ping.ping()

            # wacht op verwerking door achtergrond-taak voordat we verder gaan
            snel = str(request.POST.get('snel', ''))[:1]        # voor autotest

            if snel != '1':         # pragma: no cover
                # wacht 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0, 6.2
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('CompLaagBond:bk-teams',
                      kwargs={'deelkamp_pk': team.kampioenschap.pk})

        return HttpResponseRedirect(url)


# end of file
