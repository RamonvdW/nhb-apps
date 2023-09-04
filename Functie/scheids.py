# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de extra rechten van sporters die niet vereisen om van rol te wisselen. """

from Functie.definities import SCHEIDS_NIET


SESSIONVAR_SCHEIDS = 'gebruiker_is_scheids'


def scheids_zet_sessionvars(account, request):
    """ zet een session variabele die onthoudt of de sporter ook scheidsrechter is
    """

    print('scheids_zet_sessionvars')
    if account.is_authenticated:        # pragma: no branch
        is_scheids = account.scheids != SCHEIDS_NIET
    else:
        is_scheids = False

    request.session[SESSIONVAR_SCHEIDS] = is_scheids


def sporter_is_scheids(request):
    is_scheids = False
    if request.user.is_authenticated:
        try:
            is_scheids = request.session[SESSIONVAR_SCHEIDS]
        except KeyError:
            pass

    return is_scheids


# end of file
