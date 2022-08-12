# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Account.models import AccountSessions


SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED = "account_otp_verified"


# rechten plugins zijn functies die reageren op het veranderen van de rechten van
# een gebruiker. Typische wordt iets uitgezocht en opgeslagen in sessie variables.
account_plugins_rechten = list()

# declaratie van de rechten plugin functie:
#       def plugin(request, account):
# de plugin wordt aangeroepen na succesvolle login en na OTP controle


def account_add_plugin_rechten(func):
    """ plugin toevoegen """
    account_plugins_rechten.append(func)


def account_rechten_eval_now(request, account):
    """ opnieuw de rechten evalueren, nog login of OTP controle """
    for func in account_plugins_rechten:
        func(request, account)
    # for


def _account_rechten_change_otp_status(request, is_verified):
    """ De 2FA verificatie status is aangepast - sla dit op """
    request.session[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED] = is_verified
    account = request.user
    account_rechten_eval_now(request, account)


def account_rechten_login_gelukt(request):
    """ Deze functie wordt aangeroepen vanuit de LoginView om een sessie variabele
        te zetten die onthoudt of de gebruiker een OTP controle uitgevoerd heeft
    """
    _account_rechten_change_otp_status(request, False)

    # zorg dat nieuwe sessies al aangemaakt zijn
    if not request.session.session_key:
        request.session.save()

    # koppel de (eventuele nieuwe) sessie aan het account
    AccountSessions.objects.get_or_create(account=request.user,
                                          session_id=request.session.session_key)   # session_id = primary key


def account_rechten_otp_controle_gelukt(request):
    """ Deze functie wordt aangeroepen vanuit de OTPControleView om een sessie variabele
        te zetten die onthoudt dat de OTP-controle voor de gebruiker gelukt is
    """

    account = request.user
    account.otp_controle_gelukt_op = timezone.now()
    account.save(update_fields=['otp_controle_gelukt_op'])

    _account_rechten_change_otp_status(request, True)


def account_rechten_is_otp_verified(request):
    try:
        return request.session[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED]
    except KeyError:
        pass
    return False


# end of file
