# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de extra rechten van sporters die niet vereisen om van rol te wisselen. """

from Account.models import Account
from Account.operations import zet_sessionvar_if_changed
from BasisTypen.definities import SCHEIDS_NIET

SESSIONVAR_SCHEIDS = 'gebruiker_is_scheids'


def rol_zet_is_scheids(request, account: Account):
    """ zet een session variabele die onthoudt of de sporter ook scheidsrechter is
    """

    is_scheids = account.scheids != SCHEIDS_NIET

    zet_sessionvar_if_changed(request, SESSIONVAR_SCHEIDS, is_scheids)


def gebruiker_is_scheids(request):
    is_scheids = False
    if request.user.is_authenticated:
        try:
            is_scheids = request.session[SESSIONVAR_SCHEIDS]
        except KeyError:
            pass

    return is_scheids


# end of file
