# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import ORGANISATIES2SHORT_STR
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Wedstrijden.definities import (ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR,
                                    WEDSTRIJD_STATUS_CHOICES, WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING,
                                    WEDSTRIJD_STATUS2URL, WEDSTRIJD_URL2STATUS)
from Wedstrijden.models import Wedstrijd
from types import SimpleNamespace
import datetime

TEMPLATE_WEDSTRIJDEN_OVERZICHT_MANAGER = 'wedstrijden/overzicht-manager.dtl'


class KalenderManagerView(UserPassesTestMixin, View):
    """ Via deze view kan de Manager Competitiezaken de wedstrijdkalender beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ)

    @staticmethod
    def _maak_filter_knoppen(context, gekozen_status):
        """ filter knoppen voor de wedstrijdstatus """

        context['status_filters'] = status_filters = list()

        optie_alle = SimpleNamespace(
                            sel='status_alle',
                            beschrijving='Alle',
                            selected=True,              # fallback, kan verderop op False gezet worden
                            zoom_url=reverse('Wedstrijden:manager'))
        status_filters.append(optie_alle)

        for status, beschrijving in WEDSTRIJD_STATUS_CHOICES:       # gegarandeerde volgorde

            url_param = WEDSTRIJD_STATUS2URL[status]
            url = reverse('Wedstrijden:manager-status', kwargs={'status': url_param})
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
            status_str = kwargs['status'][:15]          # afkappen voor de veiligheid
            status = WEDSTRIJD_URL2STATUS[status_str]
        except KeyError:
            status = None

        # begin 2 maanden terug in tijd (oudere wedstrijden zijn niet interessant)
        datum_vanaf = timezone.now().date() - datetime.timedelta(days=61)

        # pak de 50 meest recente wedstrijden
        wedstrijden = (Wedstrijd
                       .objects
                       .filter(datum_begin__gte=datum_vanaf)
                       .order_by('datum_begin'))

        if status:
            wedstrijden = wedstrijden.filter(status=status)

        wedstrijden = wedstrijden[:100]

        for wed in wedstrijden:
            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wed.organisatie]
            wed.disc_str = ORGANISATIES2SHORT_STR[wed.organisatie] + ' / ' + disc2str[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.status_val_op = (wed.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING)
            wed.url_wijzig = reverse('Wedstrijden:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Wedstrijden:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        context['huidige_rol'] = rol_get_beschrijving(request)

        self._maak_filter_knoppen(context, status)

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        return render(request, self.template_name, context)


# end of file
