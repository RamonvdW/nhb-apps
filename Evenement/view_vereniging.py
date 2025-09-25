# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Evenement.definities import EVENEMENT_STATUS_TO_STR
from Evenement.models import Evenement
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
import datetime


TEMPLATE_EVENEMENT_OVERZICHT_VERENIGING = 'evenement/overzicht-vereniging.dtl'


class VerenigingEvenementenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de evenementen van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        context['ver'] = ver = self.functie_nu.vereniging

        context['huidige_rol'] = rol_get_beschrijving(request)

        now = timezone.now().date()
        jaar_geleden = now - datetime.timedelta(days=365)
        maand_geleden = now - datetime.timedelta(days=30)

        evenementen = (Evenement
                       .objects
                       .filter(organiserende_vereniging=ver)
                       .exclude(datum__lt=jaar_geleden)
                       .order_by('datum',
                                 'pk'))

        context['evenementen_actueel'] = evenementen_actueel = list()
        context['evenementen_eerder'] = evenementen_eerder = list()

        for evenement in evenementen:
            evenement.status_str = EVENEMENT_STATUS_TO_STR[evenement.status]
            evenement.url_details = reverse('Evenement:details',
                                            kwargs={'evenement_pk': evenement.pk})
            evenement.url_aanmeldingen = reverse('Evenement:aanmeldingen',
                                                 kwargs={'evenement_pk': evenement.pk})

            if evenement.workshop_keuze.strip():
                evenement.toon_workshop_keuzes = True
                evenement.url_workshop_keuzes = reverse('Evenement:workshop-keuzes',
                                                        kwargs={'evenement_pk': evenement.pk})

            if evenement.datum < maand_geleden:
                evenementen_eerder.append(evenement)
            else:
                evenementen_actueel.append(evenement)
        # for

        context['url_mollie'] = reverse('Betaal:vereniging-instellingen')
        context['url_overboeking_ontvangen'] = reverse('Bestelling:overboeking-ontvangen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (None, 'Evenementen'),
        )

        return render(request, self.template_name, context)


# end of file
