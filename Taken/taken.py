# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from .models import Taak
from datetime import timedelta


SESSIONVAR_TAAK_AANTAL_OPEN = "taak_aantal_open"
SESSIONVAR_TAAK_EVAL_AFTER = "taak_eval_after"

TAAK_EVAL_INTERVAL_MINUTES = 5


def aantal_open_taken(request):
    """ geef terug hoeveel taken er open stonden bij de laatste evaluatie """
    try:
        aantal_open = request.session[SESSIONVAR_TAAK_AANTAL_OPEN]
    except KeyError:
        aantal_open = None
    return aantal_open


def eval_open_taken(request, forceer=False):
    """ voer elke paar minuten een evaluatie uit van het aantal taken
        dat open staat voor deze gebruiker
    """
    try:
        eval_after = request.session[SESSIONVAR_TAAK_EVAL_AFTER]
    except KeyError:
        eval_after = None

    if not forceer:
        now_str = str(timezone.now().toordinal())
        if eval_after and now_str <= eval_after:
            return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    next_eval = timezone.now() + timedelta(seconds=60*TAAK_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.toordinal())
    request.session[SESSIONVAR_TAAK_EVAL_AFTER] = eval_after

    aantal_open = (Taak
                   .objects
                   .exclude(is_afgerond=True)
                   .filter(toegekend_aan=request.user)
                   .count())
    request.session[SESSIONVAR_TAAK_AANTAL_OPEN] = aantal_open

# end of file
