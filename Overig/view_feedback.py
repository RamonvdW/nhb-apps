# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect
from django.urls import Resolver404, reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics
from .forms import SiteFeedbackForm
from .models import SiteFeedback, store_feedback

TEMPLATE_FEEDBACK_FORMULIER = 'overig/site-feedback-formulier.dtl'
TEMPLATE_FEEDBACK_BEDANKT = 'overig/site-feedback-bedankt.dtl'
TEMPLATE_FEEDBACK_INZICHT = 'overig/site-feedback-inzicht.dtl'


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

        if request.user.is_authenticated:
            gebruiker_naam = request.user.get_account_full_name()
        else:
            gebruiker_naam = 'Niet bekend (anoniem)'

        # bewaar twee parameters in de sessie - deze blijven server-side
        request.session['feedback_op_pagina'] = kwargs['op_pagina']
        request.session['feedback_gebruiker'] = gebruiker_naam

        # geef het formulier aan de gebruiker om in te vullen
        form = SiteFeedbackForm(initial={'bevinding': '6'})     # TODO: werkt niet met materialcss radiobuttons
        bev = kwargs['bevinding']
        context = {'form': form,
                   'formulier_url': reverse('Overig:feedback-formulier'),     # URL voor de POST
                   'gebruiker_naam': gebruiker_naam,
                   'check_0': (bev == 'plus'),     # TODO: workaround for materializecss radiobuttons in Django
                   'check_1': (bev == 'nul'),      #       see comment in site-feedback-formulier.dtl
                   'check_2': (bev == 'min')
                  }
        menu_dynamics(request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            als de gebruiker op de Verstuur knop drukt krijgt deze functie de ingevoerde data.
        """
        form = SiteFeedbackForm(data=request.POST)
        if form.is_valid():
            try:
                op_pagina = request.session['feedback_op_pagina']
                gebruiker = request.session['feedback_gebruiker']
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
        menu_dynamics(request, context)
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
        menu_dynamics(self.request, context)
        return context


class SiteFeedbackInzichtView(UserPassesTestMixin, ListView):
    """ Deze view toont de ontvangen feedback. """

    # class variables shared by all instances
    template_name = TEMPLATE_FEEDBACK_INZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) in (Rollen.ROL_IT, Rollen.ROL_BB)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # 50 nieuwste niet-afgehandelde site feedback items
        self.count_aanwezig = SiteFeedback.objects.count()
        self.count_niet_afgehandeld = SiteFeedback.objects.filter(is_afgehandeld=False).count()
        return SiteFeedback.objects.filter(is_afgehandeld=False).order_by('-toegevoegd_op')[:50]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['count_aanwezig'] = self.count_aanwezig
        context['count_afgehandeld'] = self.count_aanwezig - self.count_niet_afgehandeld
        menu_dynamics(self.request, context)
        return context


# end of file
