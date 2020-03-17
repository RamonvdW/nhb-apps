# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from .mailer import send_mail


class MailQueue(models.Model):
    """ Database tabel waarin de te versturen emails staan """

    toegevoegd_op = models.DateTimeField()
    is_verstuurd = models.BooleanField()
    laatste_poging = models.DateTimeField()
    aantal_pogingen = models.PositiveSmallIntegerField()
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


def queue_email(to_address, onderwerp, text_body):
    """ Deze functie accepteert het verzoek om een mail te versturen en slaat deze op in de database
        Het feitelijk versturen van de email wordt door een achtergrondprocess gedaan
    """
    now = timezone.now()    # in utc

    # maak de date: header voor in de mail, in lokale tijdzone
    # formaat: Tue, 01 Jan 2020 20:00:03 +0100
    mail_date = timezone.localtime(now).strftime("%a, %d %b %Y %H:%M:%S %z")

    obj = MailQueue()
    obj.toegevoegd_op = now
    obj.is_verstuurd = False
    obj.laatste_poging = now
    obj.aantal_pogingen = 0
    obj.mail_to = to_address
    obj.mail_subj = onderwerp
    obj.mail_date = mail_date
    obj.mail_text = text_body
    obj.laaatste_poging = "-"
    obj.save()

# end of file
