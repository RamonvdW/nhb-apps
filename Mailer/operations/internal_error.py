# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.transaction import TransactionManagementError
from Mailer.models import MailQueue
from .queue import mailer_queue_email
import datetime


def mailer_notify_internal_error(tb):
    """ Deze functie stuurt een mail over een internal server error,
        maar zorgt ervoor dat er maximaal 1 mail per dag wordt gestuurd
        over hetzelfde probleem.
    """

    # kijk of hetzelfde rapport de afgelopen 24 uur al verstuurd is
    now = timezone.now()    # in utc
    recent = now - datetime.timedelta(days=1)

    try:
        count = (MailQueue
                 .objects
                 .filter(toegevoegd_op__gt=recent,
                         mail_to=settings.EMAIL_DEVELOPER_TO,
                         mail_subj=settings.EMAIL_DEVELOPER_SUBJ,
                         mail_text=tb)
                 .count())

        if count == 0:
            # nog niet gerapporteerd in de afgelopen 24 uur
            mailer_queue_email(
                    settings.EMAIL_DEVELOPER_TO,
                    settings.EMAIL_DEVELOPER_SUBJ,
                    tb,
                    enforce_whitelist=False)

    except TransactionManagementError:      # pragma: no cover
        # hier kunnen we alleen komen tijdens een autotest, welke automatisch in een atomic transaction uitgevoerd
        # wordt nadat er een database fout opgetreden is.
        # dan kunnen we geen nieuwe queries meer doen om een mail op te slaan.
        pass


# end of file
