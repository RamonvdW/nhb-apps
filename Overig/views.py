# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.urls import Resolver404, reverse
from Plein.kruimels import make_context_broodkruimels
from .forms import SiteFeedbackForm
from .models import SiteFeedback, store_feedback, SiteTijdelijkeUrl

TEMPLATE_FEEDBACK_FORMULIER = 'overig/site-feedback-formulier.dtl'
TEMPLATE_FEEDBACK_BEDANKT = 'overig/site-feedback-bedankt.dtl'


class SiteFeedbackView(View):
    """ View voor het feedback formulier
        get: radio-button wordt gezet aan de hand van de gebruikte url
        post: ingevoerde waarden worden in de database gezet
    """

    # class variables shared by all instances
    template_name = TEMPLATE_FEEDBACK_FORMULIER

    def get(self, request, *args, **kwargs):
        """
            deze functie handelt het GET verzoek af met de extra parameters (bevinding, op_pagina)
                retourneert het formulier
        """
        if 'op_pagina' not in kwargs:
            # een gebruiker kan via de POST-url voor het formulier bij deze GET functie komen
            # stuur ze weg
            raise Resolver404()

        try:
            initial_bevinding = SiteFeedback.url2bev[kwargs['bevinding']]
        except KeyError:
            # rare waarde
            initial_bevinding = SiteFeedback.url2bev['nul']
        gebruiker_naam = request.user.username
        if not gebruiker_naam:
            gebruiker_naam = 'Niet bekend (anoniem)'

        # bewaar twee parameters in de sessie - deze blijven server-side
        request.session['op_pagina'] = kwargs['op_pagina']
        request.session['gebruiker'] = gebruiker_naam

        # geef het formulier aan de gebruiker om in te vullen
        form = SiteFeedbackForm(initial={'bevinding': initial_bevinding})
        context = {'form': form,
                   'formulier_url': reverse('Overig:feedback-formulier'),     # URL voor de POST
                   'gebruiker_naam': gebruiker_naam}
        make_context_broodkruimels(context, 'Plein:plein', 'Overig:feedback-formulier')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            als de gebruiker op de Verstuur knop drukt krijgt deze functie de ingevoerde data.
        """
        form = SiteFeedbackForm(data=request.POST)
        if form.is_valid():
            try:
                op_pagina = request.session['op_pagina']
                gebruiker = request.session['gebruiker']
            except KeyError:
                pass
            else:
                store_feedback(
                    gebruiker,
                    op_pagina,
                    form.cleaned_data['bevinding'],
                    form.cleaned_data['feedback'])
                return redirect('Overig:feedback-bedankt')

        context = {'form': form,
                   'formulier_url': reverse('Overig:feedback-formulier')}  # URL voor de POST
        make_context_broodkruimels(context, 'Plein:plein', 'Overig:feedback-formulier')
        return render(request, self.template_name, context)


class SiteFeedbackBedanktView(TemplateView):
    """ Deze view wordt gebruikt nadat de gebruiker feedback geleverd heeft.
        Een statische pagina wordt getoond, met transitie terug naar het plein.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_FEEDBACK_BEDANKT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        make_context_broodkruimels(context, 'Plein:plein', 'Overig:feedback-formulier', 'Overig:feedback-bedankt')
        return context


class SiteTijdelijkeUrlView(View):
    """ Op deze view komen de tijdelijke url's uit
        We dispatchen naar de juiste afhandelaar
    """

    def get(self, request, *args, **kwargs):
        url_code = kwargs['code']
        print("get: url_code=%s" % repr(url_code))
        obj = SiteTijdelijkeUrl.objects.get(url_code=url_code)
        print("get: obj=%s" % repr(obj))

# end of file
