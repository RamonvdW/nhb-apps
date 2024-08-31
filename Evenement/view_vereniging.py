# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Evenement.definities import EVENEMENT_STATUS_TO_STR
from Evenement.models import Evenement
from Functie.definities import Rollen
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
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_SEC)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        context['ver'] = ver = self.functie_nu.vereniging

        context['huidige_rol'] = rol_get_beschrijving(request)

        datum = timezone.now().date()
        datum -= datetime.timedelta(days=30)

        evenementen = (Evenement
                       .objects
                       .filter(organiserende_vereniging=ver,
                               datum__gt=datum)
                       .order_by('datum',
                                 'pk'))

        for evenement in evenementen:
            evenement.status_str = EVENEMENT_STATUS_TO_STR[evenement.status]
            evenement.url_details = reverse('Evenement:details',
                                            kwargs={'evenement_pk': evenement.pk})
            evenement.url_aanmeldingen = reverse('Evenement:aanmeldingen',
                                                 kwargs={'evenement_pk': evenement.pk})
        # for

        context['evenementen'] = evenementen

        context['url_mollie'] = reverse('Betaal:vereniging-instellingen')
        context['url_overboeking_ontvangen'] = reverse('Bestel:overboeking-ontvangen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Evenementen'),
        )

        return render(request, self.template_name, context)


# end of file
