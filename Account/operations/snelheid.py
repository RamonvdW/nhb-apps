# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.models import AccountVerzoekenTeller
import time


def _get_hour_number():
    # get the hour number since epoch
    seconds_since_epoch = time.time()
    hours_since_epoch = int(seconds_since_epoch / 3600)
    return hours_since_epoch


def account_controleer_snelheid_verzoeken(account, limiet=100):
    """ Controleer dat de verzoeken niet te snel binnen komen

        Retourneert: True als het tempo acceptabel is
                     False als het verdacht snel gaat
    """

    uur_nummer = _get_hour_number()

    teller, is_created = AccountVerzoekenTeller.objects.get_or_create(account=account)

    if teller.uur_nummer != uur_nummer:
        teller.uur_nummer = uur_nummer
        teller.teller = 0

    teller.teller += 1
    teller.save(update_fields=['uur_nummer', 'teller'])

    return teller.teller <= limiet


# end of file
