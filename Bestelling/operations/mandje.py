# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from datetime import timedelta
from Account.models import get_account, Account
from Account.operations.session_vars import zet_sessionvar_if_changed
from Bestelling.models import BestellingMandje


SESSIONVAR_MANDJE_INHOUD_AANTAL = 'mandje_inhoud_aantal'
SESSIONVAR_MANDJE_EVAL_AFTER = 'mandje_eval_after'

MANDJE_EVAL_INTERVAL_MINUTES = 1


def cached_aantal_in_mandje_get(request):
    """ retourneer hoeveel items in het mandje zitten
        dit wordt onthouden in de sessie
    """

    try:
        aantal = request.session[SESSIONVAR_MANDJE_INHOUD_AANTAL]
    except KeyError:
        aantal = 0

    return aantal


def mandje_tel_inhoud(request, account: Account | None):
    """ tel het aantal producten in het mandje en cache het resultaat in een sessie variabele """

    if not account:
        account = get_account(request)
    try:
        mandje = (BestellingMandje
                  .objects
                  .prefetch_related('producten')
                  .get(account=account))
    except BestellingMandje.DoesNotExist:
        # geen mandje gevonden
        aantal = 0
    else:
        aantal = mandje.producten.count()

    zet_sessionvar_if_changed(request, SESSIONVAR_MANDJE_INHOUD_AANTAL, aantal)

    next_eval = timezone.now() + timedelta(seconds=60 * MANDJE_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.timestamp())     # number of seconds since 1-1-1970
    zet_sessionvar_if_changed(request, SESSIONVAR_MANDJE_EVAL_AFTER, eval_after)


def eval_mandje_inhoud(request):
    """ Als de gebruiker een tijdje weggeweest is dan kan de achtergrondtaak het mandje geleegd hebben.
        Als er dus iets in het mandje zit van deze gebruiker, kijk dan 1x per minuut of dit nog steeds zo is.
        Actief toevoegen/verwijderen leidt ook tot de evaluatie.
    """

    # kijk of het alweer tijd is
    try:
        eval_after = request.session[SESSIONVAR_MANDJE_EVAL_AFTER]
    except KeyError:
        eval_after = None

    now_str = str(timezone.now().timestamp())

    if eval_after and now_str <= eval_after:
        # nog niet
        return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    mandje_tel_inhoud(request, None)

# end of file
