# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from Instaptoets.models import Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_TO_STR
from Opleiding.models import Opleiding, OpleidingInschrijving

TEMPLATE_OPLEIDING_OVERZICHT_MANAGER = 'opleiding/overzicht-manager.dtl'
TEMPLATE_OPLEIDING_NIET_INGESCHREVEN = 'opleiding/niet-ingeschreven.dtl'


class ManagerOpleidingenView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen de opleidingen beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)

        opleidingen = (Opleiding
                       .objects
                       .order_by('periode_begin',
                                 'periode_einde',
                                 'pk'))

        for opleiding in opleidingen:
            opleiding.status_str = OPLEIDING_STATUS_TO_STR[opleiding.status]
            opleiding.url_details = reverse('Opleiding:details',
                                            kwargs={'opleiding_pk': opleiding.pk})
            opleiding.url_aanmeldingen = reverse('Opleiding:aanmeldingen',
                                                 kwargs={'opleiding_pk': opleiding.pk})
        # for

        context['opleidingen'] = opleidingen

        context['url_stats_instaptoets'] = reverse('Instaptoets:stats')
        context['url_gezakt'] = reverse('Instaptoets:gezakt')
        context['url_niet_ingeschreven'] = reverse('Opleiding:niet-ingeschreven')
        context['url_aanpassingen'] = reverse('Opleiding:aanpassingen')
        context['url_toevoegen'] = reverse('Opleiding:toevoegen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_OPLEIDINGEN_URL

        context['kruimels'] = (
            (None, 'Opleidingen'),
        )

        return render(request, self.template_name, context)


class OpleidingToevoegenView(UserPassesTestMixin, View):

    """ View deze view kan de manager een nieuwe opleiding aanmaken """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_MO

    def post(self, request, *args, **kwargs):
        now = timezone.now()
        opleiding = Opleiding(
                        laten_zien=False,
                        periode_begin=now,
                        periode_einde=now)
        opleiding.save()

        url = reverse('Opleiding:manager')
        return HttpResponseRedirect(url)


class NietIngeschrevenView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen zien wie wel de instaptoets gehaald hebben,
        maar zich niet ingeschreven hebben voor de basiscursus.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_NIET_INGESCHREVEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)

        # TODO: filteren op status, want niet elke OpleidingInschrijving is ook definitief
        ingeschreven_lid_nrs = (OpleidingInschrijving
                                .objects
                                .filter(opleiding__is_basiscursus=True)
                                .distinct('sporter')
                                .values_list('sporter__lid_nr', flat=True))

        context['niet_ingeschreven'] = lijst = list()
        for toets in (Instaptoets
                      .objects
                      .filter(is_afgerond=True,
                              geslaagd=True)
                      .select_related('sporter')
                      .order_by('-afgerond')):      # nieuwste eerst

            if toets.sporter.lid_nr not in ingeschreven_lid_nrs:
                toets.basiscursus_str = 'Niet ingeschreven'
                toets.lid_nr_en_naam = toets.sporter.lid_nr_en_volledige_naam()

                lijst.append(toets)
        # for

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Niet ingeschreven'),
        )

        return render(request, self.template_name, context)


# end of file
