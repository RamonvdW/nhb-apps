# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from TijdelijkeCodes.models import TijdelijkeCode
from TijdelijkeCodes.operations import beschrijving_activiteit, do_dispatch
from Plein.menu import menu_dynamics

TEMPLATE_CODE_GOED = 'tijdelijkecodes/code-goed.dtl'
TEMPLATE_CODE_FOUT = 'tijdelijkecodes/code-fout.dtl'


class OntvangerView(View):
    """ Op deze view komen de tijdelijke url's uit
        We dispatchen naar de juiste afhandelaar
    """

    @staticmethod
    def get(request, *args, **kwargs):
        """
            deze functie handelt het GET verzoek af met de extra parameter 'code',
            zoekt de bijbehorende data op en roept de juiste dispatcher aan.

            Om de tijdelijke URL te gebruiken moet een POST gedaan worden.
            Hiervoor bieden we een pagina met een knop aan.
        """
        url_code = kwargs['code']

        context = {
            'activiteit': '???',
            'verberg_login_knop': True,
            'url': reverse('TijdelijkeCodes:tijdelijke-url', kwargs={'code': url_code})
        }

        # kijk of deze tijdelijke url al verlopen is
        match = False
        now = timezone.now()
        for obj in TijdelijkeCode.objects.filter(url_code=url_code):
            if obj.geldig_tot > now:
                # bruikbare match gevonden
                match = True
                context['activiteit'] = beschrijving_activiteit(obj)
            else:
                # verlopen link
                obj.delete()
        # for

        if not match:
            template = TEMPLATE_CODE_FOUT
        else:
            template = TEMPLATE_CODE_GOED

        menu_dynamics(request, context)
        return render(request, template, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """
            deze functie wordt aangeroepen als op de knop GA DOOR gedrukt
            is na het volgen van een tijdelijke url.
            Zoek de bijbehorende data op en roept de juiste dispatcher aan.
        """
        url_code = kwargs['code']

        url_or_response = None
        now = timezone.now()
        for obj in TijdelijkeCode.objects.filter(url_code=url_code):
            # kijk of deze tijdelijke url al verlopen is
            if obj.geldig_tot > now:
                # dispatch naar de juiste applicatie waar deze bij hoort
                # de callbacks staan in de dispatcher
                url_or_response = do_dispatch(request, obj)

            # verwijder de gebruikte tijdelijke url
            obj.delete()
        # for

        if isinstance(url_or_response, HttpResponse):
            response = url_or_response
        else:
            if not url_or_response:
                url_or_response = reverse('Plein:plein')
            response = HttpResponseRedirect(url_or_response)

        return response

# end of file