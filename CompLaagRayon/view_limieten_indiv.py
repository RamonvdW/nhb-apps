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
from Competitie.models import CompetitieIndivKlasse
from CompLaagRayon.models import KampRK, CutRK
from CompLaagRayon.operations import maak_mutatie_kamp_rk_wijzig_indiv_cut
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek

TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_INDIV = 'complaagrayon/wijzig-limieten-indiv.dtl'


class WijzigIndivLimietenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO de limiet van individuele wedstrijdklassen aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_INDIV
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

        context['wkl_indiv'] = wkl_indiv = (CompetitieIndivKlasse
                                            .objects
                                            .filter(competitie=comp,
                                                    is_ook_voor_rk_bk=True)
                                            .select_related('boogtype')
                                            .order_by('volgorde'))

        # zet de default limieten
        pk2wkl_indiv = dict()
        for wkl in wkl_indiv:
            wkl.limiet = 24     # default limiet
            wkl.sel = 'isel_%s' % wkl.pk
            pk2wkl_indiv[wkl.pk] = wkl
        # for

        # aanvullen met de opgeslagen limieten
        for limiet in (CutRK
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kamp=deelkamp,
                               indiv_klasse__in=pk2wkl_indiv.keys())):
            wkl = pk2wkl_indiv[limiet.indiv_klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        if comp.fase_indiv < 'L':
            context['url_opslaan'] = reverse('CompLaagRayon:indiv-limieten',
                                             kwargs={'deelkamp_pk': deelkamp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'RK individuele limieten')
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
        if comp.fase_indiv >= 'L':
            raise Http404('Wijzigingen kan niet meer')

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
                    if pk2keuze_indiv[ckl.pk] not in (24, 20, 16, 12, 8, 4):
                        raise Http404('Geen valide keuze voor indiv')
        # for

        wijzig_limiet_indiv = list()     # list of tup(indiv_klasse, nieuwe_limiet, oude_limiet)

        for limiet in (CutRK
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
            except KeyError:
                pass
            else:
                # indiv klasse
                default = 24
                tup = (indiv_klasse, keuze, default)
                wijzig_limiet_indiv.append(tup)
        # for

        # laat opnieuw de deelnemers boven de cut bepalen en sorteer op gemiddelde
        door_account = get_account(request)
        door_str = "RKO %s" % door_account.volledige_naam()
        door_str = door_str[:149]

        mutaties = list()

        for indiv_klasse, nieuwe_limiet, oude_limiet in wijzig_limiet_indiv:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(indiv_klasse), str(deelkamp), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(door_account, "Competitie", msg)

                tup = (indiv_klasse, oude_limiet, nieuwe_limiet)
                mutaties.append(tup)
        # for

        snel = str(request.POST.get('snel', ''))[:1]        # voor autotest

        maak_mutatie_kamp_rk_wijzig_indiv_cut(deelkamp, mutaties, door_str, snel == '1')

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        return HttpResponseRedirect(url)


# end of file
