# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
import datetime


class LogboekRegel(models.Model):
    """ definitie van een regel in het logboek """

    # wanneer toegevoegd
    toegevoegd_op = models.DateTimeField()

    # traceerbaarheid naar een gebruiker
    actie_door_account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                           blank=True,  # allow access input in form
                                           null=True)  # allow NULL relation in database

    # welk deel van het logboek?
    gebruikte_functie = models.CharField(max_length=100)

    # de logboek regel
    # let op: bevat newlines
    activiteit = models.CharField(max_length=500)

    def bepaal_door(self):
        """ bepaal door wie actie uitgevoerd is """
        if not self.actie_door_account:
            return 'Systeem of IT beheerder'
        naam = self.actie_door_account.volledige_naam()
        # voeg inlog naam toe, indien verschillend
        # voorkom: ramon (ramon)
        if naam != self.actie_door_account.username:
            naam = "%s (%s)" % (self.actie_door_account.username, naam)
        return naam

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s (%s) %s" % (self.toegevoegd_op.strftime('%Y-%m-%d %H:%M utc'),
                               self.bepaal_door(),
                               self.gebruikte_functie)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Logboek regel"
        verbose_name_plural = "Logboek regels"

    objects = models.Manager()      # for the editor only


def schrijf_in_logboek(account: Account | None, gebruikte_functie: str, activiteit: str):
    """ Deze functie wordt gebruikt om een regel toe te voegen aan een sectie van het logboek.
    """
    obj = LogboekRegel()
    obj.toegevoegd_op = timezone.now()
    obj.actie_door_account = account
    obj.gebruikte_functie = gebruikte_functie

    # avoid exception while writing
    if len(activiteit) > 500:
        activiteit = activiteit[:500-2] + '..'

    obj.activiteit = activiteit
    obj.save()


def logboek_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen logboek entries die meer dan een jaar oud zijn
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=548)        # requirement 18 months --> 365*1.5=548

    objs = (LogboekRegel
            .objects
            .filter(toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude logboek regels' % count)
        objs.delete()


# end of file
