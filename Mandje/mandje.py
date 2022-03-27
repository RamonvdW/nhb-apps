# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from datetime import timedelta


SESSIONVAR_MANDJE_IS_LEEG = 'mandje_is_leeg'
SESSIONVAR_MANDJE_EVAL_AFTER = 'mandje_eval_after'

MANDJE_EVAL_INTERVAL_MINUTES = 1


def mandje_is_leeg(request):

    try:
        is_leeg = request.session[SESSIONVAR_MANDJE_IS_LEEG]
    except KeyError:
        is_leeg = True

    return is_leeg


def eval_mandje_is_leeg(request):
    """ Als de gebruiker een tijdje weggeweest is dan kan de achtergrondtaak het mandje leeg gemaakt
        hebben. Als er dus iets in het mandje zit van deze gebruiker, kijk dan 1x per minuut of dit
        nog steeds zo is. Actief toevoegen/verwijderen resulteert ook in de evaluatie.
    """

    try:
        is_leeg = request.session[SESSIONVAR_MANDJE_IS_LEEG]
    except KeyError:
        # niets in het mandje
        pass
    else:
        # kijk of het al weer tijd is
        try:
            eval_after = request.session[SESSIONVAR_MANDJE_EVAL_AFTER]
        except KeyError:
            eval_after = None

        now_str = str(timezone.now().toordinal())
        if eval_after and now_str <= eval_after:
            # nog niet
            return

        # update het aantal open taken in de sessie
        # en zet het volgende evaluatie moment
        next_eval = timezone.now() + timedelta(seconds=60*MANDJE_EVAL_INTERVAL_MINUTES)
        eval_after = str(next_eval.toordinal())
        request.session[SESSIONVAR_MANDJE_EVAL_AFTER] = eval_after

        aantal = (Mandje
                  .objects
                  .exclude(is_afgerond=True)
                  .filter(toegekend_aan=request.user)
                  .count())
        request.session[SESSIONVAR_MANDJE_IS_LEEG] = (aantal == 0)


# end of file
