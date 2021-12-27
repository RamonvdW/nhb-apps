# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from Plein.menu import menu_dynamics
from .models import SiteTijdelijkeUrl
from .tijdelijke_url import beschrijving_activiteit, do_dispatch

TEMPLATE_TIJDELIJKEURL_GOED = 'overig/tijdelijke-url-goed.dtl'
TEMPLATE_TIJDELIJKEURL_FOUT = 'overig/tijdelijke-url-fout.dtl'


class SiteTijdelijkeUrlView(View):
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
        context = {}
        menu_dynamics(request, context, 'hetplein')

        url_code = kwargs['code']
        context['url'] = reverse('Overig:tijdelijke-url', kwargs={'code': url_code})

        objs = SiteTijdelijkeUrl.objects.filter(url_code=url_code)

        context['activiteit'] = '???'

        # kijk of deze tijdelijke url al verlopen is
        match = False
        now = timezone.now()
        for obj in objs:
            if obj.geldig_tot > now:
                # bruikbare match gevonden
                match = True
                context['activiteit'] = beschrijving_activiteit(obj)
            else:
                # verlopen link
                obj.delete()
        # for

        if not match:
            template = TEMPLATE_TIJDELIJKEURL_FOUT
        else:
            template = TEMPLATE_TIJDELIJKEURL_GOED

        return render(request, template, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """
            deze functie wordt aangeroepen als op de knop GA DOOR gedrukt
            is na het volgen van een tijdelijke url.
            Zoek de bijbehorende data op en roept de juiste dispatcher aan.
        """
        url_code = kwargs['code']
        objs = SiteTijdelijkeUrl.objects.filter(url_code=url_code)

        # kijk of deze tijdelijke url al verlopen is
        url_or_response = None
        now = timezone.now()
        for obj in objs:
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
