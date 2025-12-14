# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.models import Count, ProtectedError
from django.utils import timezone
from Account.models import Account, AccountSessions
import datetime


def _accounts_opschonen_nieuw_niet_voltooid(stdout):
    now = timezone.now()
    wat_ouder = now - datetime.timedelta(days=3)

    # zoek gebruikers die een account aangemaakt hebben,
    # maar de mail niet binnen 3 dagen bevestigen
    # door deze te verwijderen kan de registratie opnieuw doorlopen worden
    for obj in (Account
                .objects
                .filter(email_is_bevestigd=False,
                        bevestigde_email='',
                        last_login=None,
                        date_joined__lt=wat_ouder)):

        stdout.write('[INFO] Verwijder onvoltooid account %s' % obj)
        obj.delete()
    # for


def _accounts_opschonen_geen_sporter(stdout):
    # zoek naar accounts waar niet naartoe verwezen wordt vanuit een Sporter
    for obj in (Account
                .objects
                .annotate(nr_sporters=Count('sporter'))
                .filter(nr_sporters=0)):

        try:
            stdout.write('[INFO] Verwijder spook-account %s' % obj)
            obj.delete()
        except ProtectedError as exc:
            # blokkeer inlog
            obj.is_active = False
            obj.save(update_fields=['is_active'])
            stdout.write('[INFO] Mislukt --> blokkeer spook-account %s' % obj)

            # ruim de sessies op zodat het account niet meer ingelogd is
            AccountSessions.objects.filter(account=obj).delete()
    # for


def accounts_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen nieuwe accounts die na 3 dagen nog niet voltooid zijn
        We verwijderen spook-accounts die niet meer gekoppeld zijn aan een Sporter
    """
    _accounts_opschonen_nieuw_niet_voltooid(stdout)
    _accounts_opschonen_geen_sporter(stdout)


# end of file
