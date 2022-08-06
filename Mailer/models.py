# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
import datetime


class MailQueue(models.Model):
    """ Database tabel waarin de te versturen emails staan """

    toegevoegd_op = models.DateTimeField()
    is_blocked = models.BooleanField(default=False)     # blocked door whitelist
    is_verstuurd = models.BooleanField(default=False)
    laatste_poging = models.DateTimeField()
    aantal_pogingen = models.PositiveSmallIntegerField(default=0)
    mail_to = models.CharField(max_length=150)
    mail_subj = models.CharField(max_length=100)
    mail_date = models.CharField(max_length=60)
    mail_text = models.TextField()
    log = models.TextField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "[%s] to:%s subj:'%s'" % (self.toegevoegd_op.strftime('%Y-%m-%d %H:%M utc'),
                                        self.mail_to,
                                        self.mail_subj)
        if self.is_verstuurd:
            msg = "(verstuurd) " + msg
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Mail queue"

    objects = models.Manager()      # for the editor only


def mailer_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen verstuurde emails van meer dan 3 maanden oud
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=91)

    # verwijder mails die lang geleden verstuurd zijn / hadden moeten worden
    objs = (MailQueue
            .objects
            .filter(toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude emails' % count)
        objs.delete()


# end of file
