# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import F
from .models import AccountEmail
from Plein.menu import menu_dynamics
import logging


TEMPLATE_ACTIVITEIT = 'account/activiteit.dtl'

my_logger = logging.getLogger('NHBApps.Account')


class ActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_ACTIVITEIT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        account = self.request.user
        if account.is_authenticated:
            if account.is_BB or account.is_staff:
                return True

        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nieuwe_accounts'] = (AccountEmail
                                      .objects
                                      .select_related('account')
                                      .all()
                                      .order_by('-account__date_joined')[:50])

        context['recente_activiteit'] = (AccountEmail
                                         .objects
                                         .filter(account__last_login__isnull=False)
                                         .select_related('account')
                                         .order_by('-account__last_login')[:50])

        context['inlog_pogingen'] = (AccountEmail
                                     .objects
                                     .select_related('account')
                                     .filter(account__laatste_inlog_poging__isnull=False)
                                     .filter(account__last_login__lt=F('account__laatste_inlog_poging'))
                                     .order_by('-account__laatste_inlog_poging')[:50])

        menu_dynamics(self.request, context, actief="hetplein")
        return context


# end of file
