# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

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

account_plugins_login = list()      # [tup, tup, ..] with tup = (prio, func, skip_for_login_as)


def account_add_plugin_login(prio, func, skip_for_login_as):
    tup = (prio, func, skip_for_login_as)
    account_plugins_login.append(tup)
    account_plugins_login.sort(key=lambda x: x[0])


# end of file
