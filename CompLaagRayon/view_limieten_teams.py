# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import CompetitieTeamKlasse
from CompLaagRayon.models import KampRK, CutTeamRK
from CompLaagRayon.operations import maak_mutatie_kamp_rk_wijzig_teams_cut
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek

TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_TEAMS = 'complaagrayon/wijzig-limieten-teams.dtl'


class WijzigTeamsLimietenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO de status van een RK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_TEAMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:7])  # afkappen voor de veiligheid
            deelkamp = (KampRK
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk))
        except (ValueError, KampRK.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste RKO

        comp = deelkamp.competitie
        comp.bepaal_fase()

        context['wkl_teams'] = wkl_teams = (CompetitieTeamKlasse
                                            .objects
                                            .filter(competitie=comp,
                                                    is_voor_teams_rk_bk=True)
                                            .select_related('team_type')
                                            .order_by('volgorde'))

        # zet de default limieten
        pk2klasse = dict()
        for wkl in wkl_teams:
            wkl.limiet = 8     # default limiet
            wkl.sel = 'tsel_%s' % wkl.pk
            pk2klasse[wkl.pk] = wkl
        # for

        # aanvullen met de opgeslagen limieten
        for limiet in (CutTeamRK
                       .objects
                       .select_related('team_klasse')
                       .filter(kamp=deelkamp,
                               team_klasse__in=pk2klasse.keys())):
            wkl = pk2klasse[limiet.team_klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        if comp.fase_teams < 'L':
            context['url_opslaan'] = reverse('CompLaagRayon:team-limieten',
                                             kwargs={'deelkamp_pk': deelkamp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'RK teams limieten')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:7])  # afkappen voor de veiligheid
            deelkamp = (KampRK
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk))
        except (ValueError, KampRK.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste RKO

        comp = deelkamp.competitie
        comp.bepaal_fase()
        if comp.fase_teams >= 'L':
            raise Http404('Wijzigen kan niet meer')

        pk2klasse = dict()
        pk2keuze = dict()

        for klasse in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)):

            sel = 'tsel_%s' % klasse.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze[klasse.pk] = int(keuze[:1])   # afkappen voor de veiligheid
                    pk2klasse[klasse.pk] = klasse
                except ValueError:
                    pass
                else:
                    if pk2keuze[klasse.pk] not in (8, 4):
                        raise Http404('Geen valide keuze')
        # for

        wijzig_limiet_teams = list()     # list of tup(team_klasse, nieuwe_limiet, oude_limiet)

        for limiet in (CutTeamRK
                       .objects
                       .select_related('team_klasse')
                       .filter(kamp=deelkamp,
                               team_klasse__in=list(pk2keuze.keys()))):

            pk = limiet.team_klasse.pk
            keuze = pk2keuze[pk]
            del pk2keuze[pk]

            tup = (limiet.team_klasse, keuze, limiet.limiet)
            wijzig_limiet_teams.append(tup)
        # for

        # verwerk de overgebleven keuzes waar nog geen limiet voor was
        for pk, keuze in pk2keuze.items():
            try:
                team_klasse = pk2klasse[pk]
            except KeyError:        # pragma: no cover
                pass
            else:
                default = 8
                tup = (team_klasse, keuze, default)
                wijzig_limiet_teams.append(tup)
        # for

        # vraag de achtergrondtaak de mutatie te verwerken
        door_account = get_account(request)
        door_str = "RKO %s" % door_account.volledige_naam()
        door_str = door_str[:149]

        mutaties = list()

        for team_klasse, nieuwe_limiet, oude_limiet in wijzig_limiet_teams:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(team_klasse), str(deelkamp), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(door_account, "Competitie", msg)

                tup = (team_klasse, oude_limiet, nieuwe_limiet)
                mutaties.append(tup)
        # for

        snel = str(request.POST.get('snel', ''))[:1]        # voor autotest

        maak_mutatie_kamp_rk_wijzig_teams_cut(deelkamp, mutaties, door_str, snel == '1')

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        return HttpResponseRedirect(url)


# end of file
