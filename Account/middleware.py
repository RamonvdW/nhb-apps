# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.shortcuts import reverse
from Account.models import get_account
from Account.operations.otp import otp_zet_controle_niet_gelukt
import datetime
import logging

SESSIONVAR_ACCOUNT_LOGIN_AS_DATE = 'account login-as datum'

my_logger = logging.getLogger('MH.Account')


class HerhaalLoginOTP:
    """ Deze middleware forceert nieuwe authenticatie:
        - Nieuwe inlog elke settings.HERHAAL_INTERVAL_LOGIN dagen
        - OTP controle elke settings.HERHAAL_INTERVAL_OTP dagen
    """

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        # pre-code
        if request.user.is_authenticated:
            # gebruiker is ingelogd
            account = get_account(request)
            now = timezone.now()
            login_as_date = request.session.get(SESSIONVAR_ACCOUNT_LOGIN_AS_DATE, None)
            skip_checks = False

            if login_as_date:
                # dit is een speciale login-as sessie
                date_str = now.strftime('%Y-%m-%d')
                if date_str == login_as_date:
                    skip_checks = True
                else:
                    # sessie mag niet meer gebruikt worden
                    my_logger.info('Account %s forceer einde login-as sessie' % repr(account.username))

                    # integratie met de authenticatie laag van Django
                    # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                    logout(request)

                    # redirect naar het plein
                    return HttpResponseRedirect(reverse('Plein:plein'))

            if not skip_checks:
                if account.otp_is_actief:
                    # gebruiker is een beheerder
                    if not account.otp_controle_gelukt_op:
                        # rare situatie
                        # in de sessie zeggen we dat de OTP controle nog niet gelukt is
                        otp_zet_controle_niet_gelukt(request)
                    else:
                        herhaal_na = account.otp_controle_gelukt_op + datetime.timedelta(days=settings.HERHAAL_INTERVAL_OTP)
                        if now > herhaal_na:
                            my_logger.info('Account %s forceer nieuwe OTP controle' % repr(account.username))
                            # we zetten een sessie-variabele die automatisch gebruikt wordt
                            otp_zet_controle_niet_gelukt(request)

            if not skip_checks:
                herhaal_na = account.last_login + datetime.timedelta(days=settings.HERHAAL_INTERVAL_LOGIN)
                if now > herhaal_na:
                    # inlog moet herhaald worden
                    my_logger.info('Account %s forceer nieuwe inlog' % repr(account.username))

                    # integratie met de authenticatie laag van Django
                    # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                    logout(request)

                    # redirect naar de inlog pagina
                    url = reverse('Account:login')
                    url += '?next=' + request.path
                    return HttpResponseRedirect(url)

        # roep de volgende in de keten aan (middleware of view)
        response = self._get_response(request)

        # post-code
        return response


# end of file
