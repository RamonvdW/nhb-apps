# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.templatetags.static import static
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from Competitie.models import Competitie


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        if functie_nu.nhb_ver.wedstrijdlocatie_set.count() > 0:
            locatie = functie_nu.nhb_ver.wedstrijdlocatie_set.all()[0]
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details',
                                                          kwargs={'locatie_pk': locatie.pk,
                                                                  'vereniging_pk': functie_nu.nhb_ver.pk})

        context['competities'] = Competitie.objects.filter(is_afgesloten=False)

        for comp in context['competities']:
            if comp.afstand == '18':
                comp.icon = static('plein/badge_nhb_indoor.png')
            else:
                comp.icon = static('plein/badge_nhb_25m1p.png')
        # for

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
