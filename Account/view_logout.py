# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import logout
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Overig.helpers import get_safe_from_ip
import logging


TEMPLATE_UITLOGGEN = 'account/uitloggen.dtl'

my_logger = logging.getLogger('MH.Account')


class LogoutView(UserPassesTestMixin, TemplateView):
    """
        Deze view zorgt voor het uitloggen met een POST
        Knoppen / links om uit te loggen moeten hier naartoe wijzen
    """

    # https://stackoverflow.com/questions/3521290/logout-get-or-post

    # class variables shared by all instances
    template_name = TEMPLATE_UITLOGGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user is allowed to use this view """
        # kijk of de gebruiker ingelogd is
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        """ Niet ingelogd, dus logout is niet nodig --> redirect naar het Plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Uitloggen'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is
            we zorgen voor het uitloggen en sturen door naar een andere pagina
        """

        from_ip = get_safe_from_ip(request)
        session_id = request.session.session_key
        account = get_account(request)

        my_logger.info('%s LOGOUT voor account %s' % (from_ip, repr(account.username)))
        my_logger.info('Account %s END SESSION %s' % (repr(account.username), repr(session_id)))

        # integratie met de authenticatie laag van Django
        # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
        logout(request)

        # redirect naar het plein
        return HttpResponseRedirect(reverse('Plein:plein'))


# end of file
