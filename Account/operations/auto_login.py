# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.contrib.auth import login, logout
from Account.middleware import SESSIONVAR_ACCOUNT_LOGIN_AS_DATE
from Account.models import Account
from Account.plugin_manager import account_plugins_login_gate, account_plugins_post_login
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from .session_vars import zet_sessionvar_if_changed                      # must not rely on Account.operations.__init__
from .otp import otp_zet_controle_niet_gelukt, otp_zet_controle_gelukt   # must not rely on Account.operations.__init__
import logging

my_logger = logging.getLogger('MH.Account')


def auto_login_gast_account(request, account):
    """ deze functie wordt aangeroepen vanuit een POST context om automatisch in te loggen op een gast-account.
    """
    # integratie met de authenticatie laag van Django
    login(request, account)

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog voor gast-account %s' % (
                        from_ip, repr(account.username)))

    # we slaan de typische plug-ins over omdat we geen pagina of redirect kunnen doorgeven

    otp_zet_controle_niet_gelukt(request)

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
    session_id = request.session.session_key
    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog op gast-account %s vanaf IP %s" % (
                                        repr(account.get_account_full_name()), from_ip))

    # roep de post-login plugins aan
    for _, func in account_plugins_post_login:
        # ignore redirect url returned
        _ = func(request, account)
    # for


def auto_login_lid_account_ww_vergeten(request, account: Account):
    """ deze functie wordt vanuit een POST context aangeroepen
        en logt automatisch in op het gevraagde account.

        Geeft terug:
            - None
            - of een HttpResponse object
            - of een url terug waar een http-redirect naar gedaan kan worden
    """

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog voor wachtwoord-vergeten met account %s' % (
                        from_ip, repr(account.username)))

    for _, func, skip in account_plugins_login_gate:
        if not skip:
            http_resp = func(request, from_ip, account)
            if http_resp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse that we cannot handle here

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(request)

                return http_resp

    # FUTURE: als WW vergeten via Account.nieuwe_email ging, dan kunnen we die als bevestigd markeren

    # integratie met de authenticatie laag van Django
    login(request, account)

    otp_zet_controle_niet_gelukt(request)

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    request.session['moet_oude_ww_weten'] = False

    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
    session_id = request.session.session_key
    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog op account %s vanaf IP %s" % (
                                        repr(account.get_account_full_name()), from_ip))

    # roep de post-login plugins aan
    first_url = None
    for _, func in account_plugins_post_login:
        url = func(request, account)
        if first_url is None:               # pragma: no branch
            first_url = url
    # for

    return first_url


def auto_login_as(request, account: Account):
    """ deze functie wordt vanuit een POST context aangeroepen
        en logt automatisch in op het gevraagde account.

        Geeft terug:
            - None
            - of een HttpResponse object
            - of een url terug waar een http-redirect naar gedaan kan worden
    """
    old_last_login = account.last_login
    old_otp_controle = account.otp_controle_gelukt_op

    # integratie met de authenticatie laag van Django
    logout(request)             # einde oude sessie (if any)
    login(request, account)     # maakt nieuwe sessie

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog met account %s' % (from_ip, repr(account.username)))

    for _, func, skip in account_plugins_login_gate:
        if not skip:
            http_resp = func(request, from_ip, account)
            if http_resp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse that we cannot handle here

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(request)

                return http_resp
    # for

    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
    session_id = request.session.session_key
    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

    # roep de post-login plugins aan
    for _, func in account_plugins_post_login:
        # ignore redirect url returned
        _ = func(request, account)
    # for

    if account.otp_is_actief:
        # fake de OTP passage
        otp_zet_controle_gelukt(request)
    else:
        otp_zet_controle_niet_gelukt(request)

    # herstel de last_login van de echte gebruiker
    account.last_login = old_last_login
    account.otp_controle_gelukt_op = old_otp_controle
    account.save(update_fields=['last_login', 'otp_controle_gelukt_op'])

    # sessie onthoudt dat dit een login-as sessie is
    # dit wordt gebruikt om herhaling van de OTP controle te onderdrukken
    date_str = timezone.now().strftime('%Y-%m-%d')
    zet_sessionvar_if_changed(request, SESSIONVAR_ACCOUNT_LOGIN_AS_DATE, date_str)

    # zorg dat de session-cookie snel verloopt --> nergens voor nodig
    # login-as sessie is maar 1 dag bruikbaar
    # request.session.set_expiry(0)

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog als gebruiker %s vanaf IP %s" % (repr(account.username),
                                                                                       repr(from_ip)))

    return None


# end of file
