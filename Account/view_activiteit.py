# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import F
from django.utils.timezone import make_aware
from .models import Account, AccountEmail
from Plein.menu import menu_dynamics
import datetime
import logging


TEMPLATE_ACTIVITEIT = 'account/activiteit.dtl'

my_logger = logging.getLogger('NHBApps.Account')


class ActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_ACTIVITEIT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        account = self.request.user
        if account.is_authenticated:
            if account.is_BB or account.is_staff:
                return True

        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nieuwe_accounts'] = (AccountEmail
                                      .objects
                                      .select_related('account')
                                      .all()
                                      .order_by('-account__date_joined')[:50])

        nieuwste = context['nieuwe_accounts'][0].account    # kost losse database access
        jaar = nieuwste.date_joined.year
        maand = nieuwste.date_joined.month
        deze_maand = make_aware(datetime.datetime(year=jaar, month=maand, day=1))

        context['deze_maand_count'] = (Account
                                       .objects
                                       .order_by('-date_joined')
                                       .filter(date_joined__gte=deze_maand)
                                       .count())
        context['deze_maand'] = deze_maand

        context['totaal'] = Account.objects.count()

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

        menu_dynamics(self.request, context)
        return context


# end of file
