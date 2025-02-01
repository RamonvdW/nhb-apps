# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

account_plugins_login_gate = list()   # [tup, tup, ..] with tup = (prio, func, skip_for_login_as)
account_plugins_post_login = list()   # [tup, tup, ..] with tup = (prio, func)
account_plugins_ww_vergeten = list()   # [tup, tup, ..] with tup = (prio, func)


def account_add_plugin_login_gate(prio, func, skip_for_login_as):
    """
        login plugins zijn functies die kijken of een account in mag loggen
        dit kan gebruikt worden door andere applicaties om mee te beslissen in het login process
        zonder dat er een dependencies ontstaat vanuit Account naar die applicatie

        declaratie van de login plugin functie:

           def plugin(request, from_ip, account):
               return None (mag inloggen) of HttpResponse object (mag niet inloggen)

        de plugin wordt aangeroepen na succesvolle authenticatie van username+password
        de functie render (uit django.shortcuts) produceert een HttpResponse object

        plugins are sorted on prio, lowest first
        the following blocks are defined
        10-19: Account block 1 checks (is blocked)
        20-29: other   block 1 checks (pass on new email from CRM)
        30-39: Account block 2 checks (email not accepted check)
        40-49: other   block 2 checks (leeftijdsklassen check)

    """
    tup = (prio, func, skip_for_login_as)
    account_plugins_login_gate.append(tup)
    account_plugins_login_gate.sort(key=lambda x: x[0])


def account_add_plugin_post_login(prio, func):
    """
        post-login plugins worden aangeroepen na een gelukte login.
        dit kan gebruikt worden door andere applicaties om mee te liften op het login process
        zonder dat er een dependencies ontstaat vanuit Account naar die applicatie

        de plugin kan optioneel een URL terug geven naar een nuttige pagina om de gebruiker heen te sturen.

        declaratie van de redirect plugin functie:

           def plugin(request, account):
               return url om naartoe te navigeren of None voor "geen redirect"

        de plugin wordt aangeroepen na inlog
        de functie reverse (uit django.urls) produceert url string

        plugins are sorted on prio, lowest first
        no predefined ranges
    """
    tup = (prio, func)
    account_plugins_post_login.append(tup)
    account_plugins_post_login.sort(key=lambda x: x[0])


def account_add_plugin_ww_vergeten(prio, func):
    """
        wachtwoord vergeten plugins zijn functies die een account bijwerken, bijvoorbeeld met een nieuwe e-mail.
        dit kan gebruikt worden door andere applicaties om mee te doen in het wachtwoord-vergeten process
        zonder dat er een dependencies ontstaat vanuit Account naar die applicatie

        declaratie van de ww vergeten plugin functie:

           def plugin(request, from_ip, account):
               # geen return value

        plugins are sorted on prio, lowest first
        the following blocks are defined
        10-19: Account block 1 checks (is blocked)
        20-29: other   block 1 checks (pass on new email from CRM)
    """

    tup = (prio, func)
    account_plugins_ww_vergeten.append(tup)
    account_plugins_ww_vergeten.sort(key=lambda x: x[0])


# end of file
