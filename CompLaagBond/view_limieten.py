# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView, View
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import CompetitieIndivKlasse, CompetitieTeamKlasse
from CompLaagBond.models import KampBK, CutBK
from CompLaagBond.operations import maak_mutatie_kamp_bk_wijzig_cut
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek

TEMPLATE_COMPLAAGBOND_WIJZIG_LIMIETEN = 'complaagbond/wijzig-limieten.dtl'


class WijzigLimietenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de status van een BK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPLAAGBOND_WIJZIG_LIMIETEN
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
            deelkamp_pk = int(kwargs['deelkamp_pk'][:7])  # afkappen voor de veiligheid
            deelkamp = (KampBK
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk))
        except (ValueError, KampBK.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise Http404('Niet de beheerder')

        comp = deelkamp.competitie
        if comp.is_25m1pijl():
            indiv_limieten = settings.COMPETITIE_25M_INDIV_LIMIETEN
        else:
            indiv_limieten = settings.COMPETITIE_18M_INDIV_LIMIETEN

        context['indiv_limieten'] = indiv_limieten

        context['wkl_indiv'] = wkl_indiv = (CompetitieIndivKlasse
                                            .objects
                                            .filter(competitie=deelkamp.competitie,
                                                    is_ook_voor_rk_bk=True)
                                            .select_related('boogtype')
                                            .order_by('volgorde'))

        context['wkl_teams'] = wkl_teams = (CompetitieTeamKlasse
                                            .objects
                                            .filter(competitie=deelkamp.competitie,
                                                    is_voor_teams_rk_bk=True)
                                            .order_by('volgorde'))

        # zet de default limieten
        pk2wkl_indiv = dict()
        for wkl in wkl_indiv:
            wkl.limiet = 24     # default limiet
            wkl.sel = 'isel_%s' % wkl.pk
            pk2wkl_indiv[wkl.pk] = wkl
        # for

        pk2wkl_team = dict()
        for wkl in wkl_teams:
            # ERE klasse: 12 teams
            # overige: 8 teams
            wkl.limiet = 12 if "ERE" in wkl.beschrijving else 8
            wkl.sel = 'tsel_%s' % wkl.pk
            pk2wkl_team[wkl.pk] = wkl
        # for

        # aanvullen met de opgeslagen limieten
        for limiet in (CutBK
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kamp=deelkamp,
                               indiv_klasse__in=pk2wkl_indiv.keys())):
            wkl = pk2wkl_indiv[limiet.indiv_klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        context['url_opslaan'] = reverse('CompLaagBond:wijzig-limieten',
                                         kwargs={'deelkamp_pk': deelkamp.pk})

        comp = deelkamp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'BK limieten')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:7])  # afkappen voor de veiligheid
            deelkamp = (KampBK
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk))
        except (ValueError, KampBK.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise Http404('Niet de beheerder')

        comp = deelkamp.competitie
        if comp.is_25m1pijl():
            indiv_limieten = settings.COMPETITIE_25M_INDIV_LIMIETEN
        else:
            indiv_limieten = settings.COMPETITIE_18M_INDIV_LIMIETEN

        pk2ckl_indiv = dict()
        pk2keuze_indiv = dict()

        for ckl in (CompetitieIndivKlasse
                    .objects
                    .filter(competitie=comp,
                            is_ook_voor_rk_bk=True)):

            sel = 'isel_%s' % ckl.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze_indiv[ckl.pk] = int(keuze[:2])   # afkappen voor de veiligheid
                    pk2ckl_indiv[ckl.pk] = ckl
                except ValueError:
                    pass
                else:
                    if pk2keuze_indiv[ckl.pk] not in indiv_limieten:
                        raise Http404('Geen valide keuze voor indiv limiet')
        # for

        wijzig_limiet_indiv = list()     # list of tup(indiv_klasse, nieuwe_limiet, oude_limiet)

        for limiet in (CutBK
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kamp=deelkamp,
                               indiv_klasse__in=list(pk2keuze_indiv.keys()))):

            pk = limiet.indiv_klasse.pk
            keuze = pk2keuze_indiv[pk]
            del pk2keuze_indiv[pk]

            tup = (limiet.indiv_klasse, keuze, limiet.limiet)
            wijzig_limiet_indiv.append(tup)
        # for

        # verwerk de overgebleven keuzes waar nog geen limiet voor was
        for pk, keuze in pk2keuze_indiv.items():
            try:
                indiv_klasse = pk2ckl_indiv[pk]
            except KeyError:        # pragma: no cover
                pass
            else:
                # indiv klasse
                default = 24
                tup = (indiv_klasse, keuze, default)
                wijzig_limiet_indiv.append(tup)
        # for

        # laat opnieuw de deelnemers boven de cut bepalen en sorteer op gemiddelde
        door_account = get_account(request)
        door_str = "BKO %s" % door_account.volledige_naam()
        door_str = door_str[:149]

        mutatie_lijst = list()

        for indiv_klasse, nieuwe_limiet, oude_limiet in wijzig_limiet_indiv:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(indiv_klasse), str(deelkamp), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(door_account, "Competitie", msg)

                tup = (indiv_klasse, oude_limiet, nieuwe_limiet)
                mutatie_lijst.append(tup)
        # for

        snel = str(request.POST.get('snel', ''))[:1]  # voor autotest

        maak_mutatie_kamp_bk_wijzig_cut(deelkamp, mutatie_lijst, door_str, snel == '1')

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)


# end of file
