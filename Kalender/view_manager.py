# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import ORGANISATIES2SHORT_STR
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from .models import (KalenderWedstrijd,
                     ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR, WEDSTRIJD_STATUS,
                     WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING)
from types import SimpleNamespace

TEMPLATE_KALENDER_OVERZICHT_MANAGER = 'kalender/overzicht-manager.dtl'


# vertaling van wedstrijd status in een url parameter en terug
WEDSTRIJD_STATUS2URL = { key: beschrijving.split()[0].lower() for key, beschrijving in WEDSTRIJD_STATUS }

WEDSTRIJD_URL2STATUS = { value: key for key, value in WEDSTRIJD_STATUS2URL.items() }
WEDSTRIJD_URL2STATUS['alle'] = None


class KalenderManagerView(UserPassesTestMixin, View):
    """ Via deze view kan de Manager Competitiezaken de wedstrijdkalender beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BB

    @staticmethod
    def _maak_filter_knoppen(context, gekozen_status):
        """ filter knoppen voor de wedstrijdstatus """

        context['status_filters'] = status_filters = list()

        optie_alle = SimpleNamespace(
                            sel='status_alle',
                            beschrijving='Alle',
                            selected=True,              # fallback, kan verderop op False gezet worden
                            zoom_url=reverse('Kalender:manager'))
        status_filters.append(optie_alle)

        for status, beschrijving in WEDSTRIJD_STATUS:       # gegarandeerde volgorde

            url_param = WEDSTRIJD_STATUS2URL[status]
            url = reverse('Kalender:manager-status', kwargs={'status': url_param})
            selected = (status == gekozen_status)

            if selected:
                optie_alle.selected = False

            optie = SimpleNamespace(
                            sel='status_%s' % url_param,
                            beschrijving=beschrijving,
                            selected=selected,
                            zoom_url=url)

            status_filters.append(optie)
        # for

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            status_str = kwargs['status'][:10]          # afkappen voor de veiligheid
            status = WEDSTRIJD_URL2STATUS[status_str]
        except KeyError:
            status = None

        # pak de 50 meest recente wedstrijden
        wedstrijden = (KalenderWedstrijd
                       .objects
                       .order_by('-datum_begin'))

        if status:
            wedstrijden = wedstrijden.filter(status=status)

        wedstrijden = wedstrijden[:50]

        for wed in wedstrijden:
            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wed.organisatie]
            wed.disc_str = ORGANISATIES2SHORT_STR[wed.organisatie] + ' / ' + disc2str[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.status_val_op = (wed.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING)
            wed.url_wijzig = reverse('Kalender:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Kalender:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        context['huidige_rol'] = rol_get_beschrijving(request)

        self._maak_filter_knoppen(context, status)

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)


# end of file
