# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.operations import get_sporter
from Spelden.models import SpeldAanvraagPrep


class BestelStap0View(View):

    """ In deze view stuur de gebruiker naar de juiste stap in het bestelproces """

    def get(self, request, *args, **kwargs):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionDenied('Niet ingelogd')

        if not settings.TOON_SPELDEN_BESTELLEN:
            raise Http404('Bestellen is niet mogelijk')

        account = get_account(self.request)
        sporter = get_sporter(account)
        if not sporter:                                 # pragma: no branch
            raise Http404('Onvolledige verzoek')        # pragma: no cover

        prep = SpeldAanvraagPrep.objects.filter(voor_sporter=sporter).select_related('voor_sporter').first()
        url = reverse('Spelden:bestel-stap1')

        if prep:
            if prep.heeft_data_stap3:
                url = reverse('Spelden:bestel-stap4')
            elif prep.heeft_data_stap2:
                url = reverse('Spelden:bestel-stap3')
            elif prep.heeft_data_stap1:
                url = reverse('Spelden:bestel-stap2')

        return HttpResponseRedirect(url)


# end of file
