# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from .models import Taak
from Taken.operations import eval_open_taken


TEMPLATE_OVERZICHT = 'taken/overzicht.dtl'
TEMPLATE_DETAILS = 'taken/details.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders met taken """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB,
                          Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                          Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = self.request.user

        # haal de taken op (maximaal 50)
        # zorg dat alle open taken in beeld komen door te sorteren op is_afgerond
        context['taken'] = (Taak
                            .objects
                            .filter(toegekend_aan=account)
                            .order_by('is_afgerond', 'deadline')[:50])

        count_open = count_afgerond = 0
        for taak in context['taken']:
            if taak.is_afgerond:
                count_afgerond += 1
            else:
                count_open += 1

            taak.url = reverse('Taken:details', kwargs={'taak_pk': taak.pk})
        # for

        context['heeft_open_taken'] = (count_open > 0)
        context['heeft_afgeronde_taken'] = (count_afgerond > 0)

        eval_open_taken(self.request)

        context['kruimels'] = (
            (None, 'Taken'),
        )

        menu_dynamics(self.request, context)
        return context


class DetailsView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders met taken """

    # class variables shared by all instances
    template_name = TEMPLATE_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB,
                          Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                          Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            taak_pk = int(kwargs['taak_pk'][:6])        # afkappen voor de veiligheid
            taak = (Taak
                    .objects
                    .select_related('deelcompetitie',
                                    'toegekend_aan',
                                    'aangemaakt_door')
                    .get(pk=taak_pk))
        except (ValueError, Taak.DoesNotExist):
            raise Http404('Geen valide taak')

        account = self.request.user

        # controleer dat deze taak bij de beheerder hoort
        if taak.toegekend_aan != account:
            raise PermissionDenied('Geen taak voor jouw account')

        if taak.handleiding_pagina:
            taak.url_handleiding = reverse('Handleiding:%s' % taak.handleiding_pagina)

        if not taak.is_afgerond:
            taak.url_sluiten = reverse('Taken:details', kwargs={'taak_pk': taak.pk})

        context['taak'] = taak

        context['kruimels'] = (
            (reverse('Taken:overzicht'), 'Taken'),
            (None, 'Details')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):

        try:
            taak_pk = int(kwargs['taak_pk'][:6])    # afkappen voor de veiligheid
            taak = Taak.objects.get(pk=taak_pk)
        except (ValueError, Taak.DoesNotExist):
            raise Http404('Geen valide taak')

        account = self.request.user

        # controleer dat deze taak bij de beheerder hoort
        if taak.toegekend_aan != account:
            raise PermissionDenied('Geen taak voor jouw account')

        if not taak.is_afgerond:
            if taak.log != "":
                taak.log += "\n"
            taak.log += "\n[%s] %s heeft deze taak gesloten" % (timezone.now(), account)
            taak.is_afgerond = True
            taak.save()

            eval_open_taken(request, forceer=True)

        return HttpResponseRedirect(reverse('Taken:overzicht'))

# end of file
