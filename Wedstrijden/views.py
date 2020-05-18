# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from .models import WedstrijdLocatie
from .forms import WedstrijdLocatieForm


TEMPLATE_LOCATIES = 'wedstrijden/locaties.dtl'
TEMPLATE_LOCATIE_DETAILS = 'wedstrijden/locatie-details.dtl'


class WedstrijdLocatiesView(UserPassesTestMixin, TemplateView):

    """ Deze view toon relevante wedstrijdlocaties aan beheerders """

    # class variables shared by all instances
    template_name = TEMPLATE_LOCATIES

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        objs = WedstrijdLocatie.objects.exclude(zichtbaar=False).order_by('pk')
        for obj in objs:
            obj.nhb_ver = [str(ver) for ver in obj.verenigingen.order_by('nhb_nr')]
            obj.details_url = reverse('Wedstrijden:locatie-details', kwargs={'locatie_pk': obj.pk})
        # for
        context['locaties'] = objs

        menu_dynamics(self.request, context, actief='hetplein')
        return context


class WedstrijdLocatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een wedstrijdlocatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_LOCATIE_DETAILS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        locatie_pk = kwargs['locatie_pk']
        try:
            context['locatie'] = locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        if locatie.baan_type == 'O':
            locatie.baan_type_str = 'Binnen, volledig overdekt'
        elif locatie.baan_type == 'H':
            locatie.baan_type_str = 'Half overdekt (binnen-buiten schieten)'
        else:
            locatie.baan_type_str = 'Onbekend'

        locatie.nhb_ver = [str(ver) for ver in locatie.verenigingen.order_by('nhb_nr')]

        context['opslaan_url'] = reverse('Wedstrijden:locatie-details', kwargs=kwargs)
        context['terug_url'] = reverse('Wedstrijden:locaties')

        # aantal banen waar uit gekozen kan worden
        context['banen'] = [nr for nr in range(2, 25)]

        menu_dynamics(self.request, context, actief='hetplein')
        return context

    def post(self, request, *args, **kwargs):
        locatie_pk = kwargs['locatie_pk']
        try:
            locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        form = WedstrijdLocatieForm(request.POST)
        if not form.is_valid():
            raise Resolver404()

        locatie.baan_type = form.cleaned_data.get('baan_type')
        locatie.banen_18m = form.cleaned_data.get('banen_18m')
        locatie.banen_25m = form.cleaned_data.get('banen_25m')
        locatie.max_dt_per_baan = form.cleaned_data.get('max_dt')
        locatie.notities = form.cleaned_data.get('notities')
        locatie.save()

        return HttpResponseRedirect(reverse('Wedstrijden:locaties'))

# end of file
