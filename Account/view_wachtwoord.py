# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from .models import AccountEmail
from Overig.tijdelijke_url import (set_tijdelijke_url_receiver,
                                   RECEIVER_BEVESTIG_ACCOUNT_EMAIL, RECEIVER_ACCOUNT_WISSEL,
                                   maak_tijdelijke_url_accountwissel, maak_tijdelijke_url_account_email)
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Mailer.models import mailer_queue_email, mailer_email_is_valide
import logging


TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'

my_logger = logging.getLogger('NHBApps.Account')


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief="inloggen")
        return context


# end of file
