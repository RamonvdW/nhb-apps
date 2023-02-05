# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect
from django.urls import Resolver404, reverse
from django.http import Http404
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Feedback.forms import FeedbackForm
from Feedback.models import Feedback
from Feedback.operations import store_feedback

TEMPLATE_FEEDBACK_FORMULIER = 'feedback/formulier.dtl'
TEMPLATE_FEEDBACK_BEDANKT = 'feedback/bedankt.dtl'
TEMPLATE_FEEDBACK_INZICHT = 'feedback/inzicht.dtl'


class KrijgFeedbackView(UserPassesTestMixin, View):
    """ View voor het feedback formulier
        get: radio-button wordt gezet aan de hand van de gebruikte url
        post: ingevoerde waarden worden in de database gezet
    """

    # class variables shared by all instances
    template_name = TEMPLATE_FEEDBACK_FORMULIER
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated

    def get(self, request, *args, **kwargs):
        """
            deze functie handelt het GET verzoek af met de extra parameters (bevinding, op_pagina)
                retourneert het formulier
        """
        if 'op_pagina' not in kwargs:
            # een gebruiker kan via de formulier-url bij deze GET functie komen
            # stuur ze weg
            raise Resolver404()

        gebruiker_str = request.user.get_account_full_name()
        rol_str = rol_get_beschrijving(request)

        # bewaar twee parameters in de sessie - deze blijven server-side
        request.session['feedback_op_pagina'] = kwargs['op_pagina']
        request.session['feedback_volledige_url'] = '/' + kwargs['volledige_url'] + '/'
        request.session['feedback_gebruiker'] = gebruiker_str
        request.session['feedback_in_rol'] = rol_str

        # geef het formulier aan de gebruiker om in te vullen
        form = FeedbackForm(initial={'bevinding': '6'})
        bev = kwargs['bevinding']
        context = {'form': form,
                   'formulier_url': reverse('Feedback:formulier'),     # URL voor de POST
                   'gebruiker_naam': gebruiker_str,
                   'check_0': (bev == 'plus'),
                   'check_1': (bev == 'nul'),
                   'check_2': (bev == 'min')}

        # bewust geen broodkruimels (behalve de "vorige" knop)
        # context['kruimels'] = (
        #     (None, 'Geef feedback'),
        # )

        menu_dynamics(request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            als de gebruiker op de Verstuur knop drukt krijgt deze functie de ingevoerde data.
        """

        try:
            rol_str = request.session['feedback_in_rol']
            op_pagina = request.session['feedback_op_pagina']
            gebruiker_str = request.session['feedback_gebruiker']
            volledige_url = request.session['feedback_volledige_url']
        except KeyError:
            raise Http404('Verkeerd gebruik')

        form = FeedbackForm(data=request.POST)
        if form.is_valid():
            store_feedback(
                gebruiker_str,
                rol_str,
                op_pagina,
                volledige_url,
                form.cleaned_data['bevinding'],
                form.cleaned_data['feedback'])
            return redirect('Feedback:bedankt')

        # geef het formulier aan de gebruiker om in te vullen
        # alleen hebben we hier niet onthouden welke plaatje de gebruiker aangeklikt heeft
        form = FeedbackForm(initial={'bevinding': '6'})
        context = {'form': form,
                   'formulier_url': reverse('Feedback:formulier'),     # URL voor de POST
                   'gebruiker_naam': gebruiker_str,
                   'check_0': False,
                   'check_1': True,
                   'check_2': False}

        # bewust geen broodkruimels (behalve de "vorige" knop)

        menu_dynamics(request, context)
        return render(request, self.template_name, context)


class BedanktView(TemplateView):
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


class InzichtView(UserPassesTestMixin, ListView):
    """ Deze view toont de ontvangen feedback. """

    # class variables shared by all instances
    template_name = TEMPLATE_FEEDBACK_INZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_SUP)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # 100 nieuwste niet-afgehandelde site feedback items
        return Feedback.objects.filter(is_afgehandeld=False).order_by('-toegevoegd_op')[:100]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        count_niet_afgehandeld = Feedback.objects.filter(is_afgehandeld=False).count()
        context['count_aanwezig'] = count_aanwezig = Feedback.objects.count()
        context['count_afgehandeld'] = count_aanwezig - count_niet_afgehandeld

        if self.request.user.is_staff:
            context['url_admin_site'] = reverse('admin:Feedback_feedback_changelist')

        context['kruimels'] = (
            (None, 'Feedback'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
