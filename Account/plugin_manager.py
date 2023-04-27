# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

account_plugins_login_gate = list()   # [tup, tup, ..] with tup = (prio, func, skip_for_login_as)
account_plugins_post_login = list()   # [tup, tup, ..] with tup = (prio, func)
account_plugins_eval_rights = list()  # [func, func, ..]


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


def account_add_plugin_bepaal_rechten(func):
    """
        plugins zijn functies die aangeroepen worden om de rechten van de gebruiker
        te evalueren en de resultaten te cachen in sessie variabelen.

        deze plugins worden aangeroepen na:
        - login gelukt
        - OTP controle gelukt

        declaratie van de post-login plugin functie:
            def plugin(request, account):
    """
    account_plugins_eval_rights.append(func)


def account_add_plugin_post_login_redirect(prio, func):
    """
        redirect plugins zijn functies die helpen om de gebruiker na inlog
        naar een nuttige pagina te sturen.
        dit kan gebruikt worden door andere applicaties om mee te beslissen in het login process
        zonder dat er een dependencies ontstaat vanuit Account naar die applicatie

        declaratie van de redirect plugin functie:

           def plugin(request, account):
               return None (geen redirect) of url om naartoe te navigeren

        de plugin wordt aangeroepen na inlog
        de functie reverse (uit django.urls) produceert url string

        plugins are sorted on prio, lowest first
        no predefined ranges
    """
    tup = (prio, func)
    account_plugins_post_login.append(tup)
    account_plugins_post_login.sort(key=lambda x: x[0])


def account_rechten_eval_now(request, account):
    """ opnieuw de rechten van de gebruiker evalueren,
        na login, OTP controle of VHPG controle
    """
    for func in account_plugins_eval_rights:
        func(request, account)
    # for


# end of file
