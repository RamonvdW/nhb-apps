# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import GESLACHT2STR
from Functie.rol import rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Registreer.models import GastRegistratie

TEMPLATE_GAST_ACCOUNTS = 'vereniging/gast-accounts.dtl'
TEMPLATE_GAST_ACCOUNT_DETAILS = 'vereniging/gast-account-details.dtl'


class GastAccountsView(UserPassesTestMixin, ListView):
    """ Deze view laat de SEC van vereniging 8000 de gast-accounts lijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNTS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs = (GastRegistratie
                .objects
                .select_related('sporter',
                                'account')
                .order_by('-aangemaakt'))       # nieuwste eerst

        for gast in objs:
            sporter = gast.sporter
            account = gast.account

            # zoek de laatste-inlog bij elk lid
            # SEC mag de voorkeuren van de sporters aanpassen
            gast.url_details = reverse('Vereniging:gast-account-details',
                                       kwargs={'lid_nr': gast.lid_nr})

            if account:
                if account.last_login:
                    gast.laatste_inlog = gast.account.last_login
                else:
                    gast.geen_inlog = 2
            else:
                gast.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, "Gast accounts")
        )

        menu_dynamics(self.request, context)
        return context


class GastAccountDetailsView(UserPassesTestMixin, TemplateView):
    """ Deze view laat de SEC van vereniging 8000 de details van een gast-accounts zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNT_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        lid_nr = kwargs['lid_nr'][:6]       # afkappen voor extra veiligheid
        try:
            lid_nr = int(lid_nr)
            gast = GastRegistratie.objects.get(lid_nr=lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Slechte parameter')

        gast.geslacht_str = GESLACHT2STR[gast.geslacht]
        context['gast'] = gast

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, "Gast account details")
        )

        menu_dynamics(self.request, context)
        return context


# end of file
