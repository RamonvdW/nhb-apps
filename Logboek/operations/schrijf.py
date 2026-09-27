# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Account.models import Account
from Logboek.models import LogboekRegel, MAX_LEN_ACTIVITEIT, MAX_LEN_GEBRUIKTE_FUNCTIE


def schrijf_in_logboek(account: Account | None, gebruikte_functie: str, activiteit: str):
    """ Voeg een regel toe aan het logboek """

    # avoid exception while saving
    if len(activiteit) > MAX_LEN_ACTIVITEIT:
        activiteit = activiteit[:MAX_LEN_ACTIVITEIT-2] + '..'

    if len(gebruikte_functie) > MAX_LEN_GEBRUIKTE_FUNCTIE:
        gebruikte_functie = gebruikte_functie[:MAX_LEN_GEBRUIKTE_FUNCTIE-2] + '..'

    LogboekRegel.objects.create(
            activiteit=activiteit,
            toegevoegd_op=timezone.now(),
            gebruikte_functie=gebruikte_functie,
            actie_door_account=account)


# end of file
