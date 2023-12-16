# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
import datetime


class MailQueue(models.Model):
    """ Database tabel waarin de te versturen emails staan """

    toegevoegd_op = models.DateTimeField()

    # admin
    is_blocked = models.BooleanField(default=False)     # blocked door whitelist
    is_verstuurd = models.BooleanField(default=False)

    # verzenden naar service provider
    laatste_poging = models.DateTimeField()
    aantal_pogingen = models.PositiveSmallIntegerField(default=0)

    # mail headers
    mail_to = models.CharField(max_length=150)
    mail_subj = models.CharField(max_length=100)
    mail_date = models.CharField(max_length=60)

    # mail body, text
    mail_text = models.TextField()

    # mail body, html
    mail_html = models.TextField(default='')

    # logboekje
    log = models.TextField(blank=True)

    # voor assert_email_html_ok en assert_consistent_email_text
    template_used = models.CharField(max_length=100, default='')

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "[%s] to:%s subj:'%s'" % (timezone.localtime(self.toegevoegd_op).strftime('%Y-%m-%d %H:%M'),
                                        self.mail_to,
                                        self.mail_subj)
        if self.is_verstuurd:
            msg = "(verstuurd) " + msg
        elif self.is_blocked:
            msg = "[BLOCKED] " + msg
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
