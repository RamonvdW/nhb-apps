# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from datetime import timedelta
from .models import MandjeInhoud


SESSIONVAR_MANDJE_INHOUD_AANTAL = 'mandje_inhoud_aantal'
SESSIONVAR_MANDJE_EVAL_AFTER = 'mandje_eval_after'

MANDJE_EVAL_INTERVAL_MINUTES = 1


def mandje_inhoud_aantal(request):
    """ retourneer hoeveel items in het mandje zitten
        dit wordt onthouden in de sessie
    """

    try:
        aantal = request.session[SESSIONVAR_MANDJE_INHOUD_AANTAL]
    except KeyError:
        aantal = 0

    return aantal


def mandje_heeft_toevoeging(request):
    """ zet de vlag die onthoudt dat er iets in het mandje zit """

    aantal = (MandjeInhoud
              .objects
              .filter(account=request.user)
              .count())
    request.session[SESSIONVAR_MANDJE_INHOUD_AANTAL] = aantal

    next_eval = timezone.now() + timedelta(seconds=60 * MANDJE_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.timestamp())     # number of seconds since 1-1-1970
    request.session[SESSIONVAR_MANDJE_EVAL_AFTER] = eval_after


def eval_mandje_inhoud(request):
    """ Als de gebruiker een tijdje weggeweest is dan kan de achtergrondtaak het mandje geleegd hebben.
        Als er dus iets in het mandje zit van deze gebruiker, kijk dan 1x per minuut of dit nog steeds zo is.
        Actief toevoegen/verwijderen resulteert ook in de evaluatie.
    """

    # kijk of het al weer tijd is
    try:
        eval_after = request.session[SESSIONVAR_MANDJE_EVAL_AFTER]
    except KeyError:
        eval_after = None
    else:
        # TODO: verwijder deze tijdelijke code
        if eval_after.find('.') < 0:
            eval_after = None

    now_str = str(timezone.now().timestamp())

    # print('eval_after=%s, now=%s' % (eval_after, now_str))

    if eval_after and now_str <= eval_after:
        # nog niet
        return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    mandje_heeft_toevoeging(request)


# end of file
