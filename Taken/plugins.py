# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.models import Account
from Account.plugin_manager import account_add_plugin_post_login
from Taken.operations import eval_open_taken

"""
    registratie van de plugins bij importeren van dit bestaand
    import in Taken.apps.ready
"""


def taken_login_plugin(request, _account: Account):
    """ Deze functie wordt aangeroepen vanuit de Account login view

        Hier controleren we of het lid open taken heeft en slaan dit op in de sessie

        Return: None = mag wel inloggen
    """

    eval_open_taken(request, forceer=True)

    # gebruiker mag inloggen
    return None


# registreer de plugin
account_add_plugin_post_login(80, taken_login_plugin)


# end of file
