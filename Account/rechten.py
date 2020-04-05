# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED = "account_otp_verified"


# TODO: overweeg om Django Signals te gebruiken
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
    request.session[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED] = is_verified
    account = request.user
    account_rechten_eval_now(request, account)


def account_rechten_login_gelukt(request):
    """ Deze functie wordt aangeroepen vanuit de LoginView om een sessie variabele
        te zetten die onthoudt of de gebruiker een OTP controle uitgevoerd heeft
    """
    _account_rechten_change_otp_status(request, False)


def account_rechten_otp_controle_gelukt(request):
    """ Deze functie wordt aangeroepen vanuit de OTPControleView om een sessie variabele
        te zetten die onthoudt dat de OTP controle voor de gebruiker gelukt is
    """
    _account_rechten_change_otp_status(request, True)


def account_rechten_is_otp_verified(request):
    try:
        return request.session[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED]
    except KeyError:
        pass
    return False


# end of file
