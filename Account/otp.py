# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.rechten import account_rechten_otp_controle_gelukt
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
import pyotp
import logging

my_logger = logging.getLogger('NHBApps.Account')


def account_otp_is_gekoppeld(account):
    return account.otp_is_actief


def account_otp_prepare_koppelen(account):
    """ Als het account nog niet voorbereid is voor OTP, maak het dan in orde
    """
    # maak eenmalig het OTP geheim aan voor deze gebruiker
    if len(account.otp_code) != 16:
        account.otp_code = pyotp.random_base32()
        account.save()


def account_otp_controleer(request, account, code):
    """ deze functie controleert de opgegeven account code
        als deze klopt, dan worden extra rechten vrijgegeven
        als de control mislukt, dan wordt dit in het logboek geschreven

        Returns: True:  Gelukt
                 False: Mislukt
    """
    from_ip = get_safe_from_ip(request)

    otp = pyotp.TOTP(account.otp_code)
    # valid_window=1 staat toe dat er net een nieuwe code gegenereerd is tijdens het intikken van de code
    is_valid = otp.verify(code, valid_window=1)

    if is_valid:
        # controle is gelukt
        account_rechten_otp_controle_gelukt(request)
        my_logger.info('%s 2FA controle gelukt voor account %s' % (from_ip, account.username))
        return True

    # controle is mislukt - schrijf dit in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="OTP controle",
                       activiteit='Gebruiker %s OTP controle mislukt vanaf IP %s' % (repr(account.username), from_ip))
    my_logger.info('%s 2FA mislukte controle voor account %s' % (from_ip, account.username))
    return False


def account_otp_koppel(request, account, code):
    """ Breng de 2FA koppeling tot stand als de juiste code opgegeven is

        als deze klopt, dan wordt koppeling vastgelegd en extra rechten vrijgegeven
        als de control mislukt, dan wordt dit in het logboek geschreven

        Returns: True:  Gelukt
                 False: Mislukt
    """
    from_ip = get_safe_from_ip(request)

    otp = pyotp.TOTP(account.otp_code)
    # valid_window=1 staat toe dat er net een nieuwe code gegenereerd is tijdens het intikken van de code
    is_valid = otp.verify(code, valid_window=1)

    if is_valid:
        # controle is gelukt --> koppeling maken
        account.otp_is_actief = True
        account.save()
        my_logger.info('%s 2FA koppeling gelukt voor account %s' % (from_ip, account.username))
        return True

    # controle is mislukt - schrijf dit in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="OTP controle",
                       activiteit='Gebruiker %s OTP koppeling controle mislukt vanaf IP %s' % (
                       repr(account.username), from_ip))
    my_logger.info('%s 2FA koppeling mislukte controle voor account %s' % (from_ip, account.username))


# end of file
