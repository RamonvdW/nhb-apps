# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from Functie.models import Functie
import datetime


class Taak(models.Model):

    """ Bijhouden van een specifieke taak """

    # is de taak afgehandeld / klaar, of nog niet?
    is_afgerond = models.BooleanField(default=False)

    # welke functie moet actie ondernemen / bij wie op de takenlijst zetten?
    toegekend_aan_functie = models.ForeignKey(Functie, on_delete=models.SET_NULL,
                                              null=True, blank=True,
                                              related_name='functie_taken')

    # wanneer moet het af zijn?
    deadline = models.DateField()

    # wie heeft hier om gevraagd
    # null/None = Systeem
    aangemaakt_door = models.ForeignKey(Account, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='account_taken_aangemaakt')

    # een korte versie van de taak die we kunnen tonen in de takenlijst en de e-mail
    onderwerp = models.CharField(max_length=100, default='')

    # beschrijving van de uit te voeren taak
    beschrijving = models.TextField(max_length=5000)

    # geschiedenis van deze taak
    log = models.TextField(max_length=5000, blank=True)

    def __str__(self):
        msg = "[" + self.toegekend_aan_functie.kort() + "] "
        if self.is_afgerond:
            msg += "(afgerond) "
        return msg + self.onderwerp

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Taak"
        verbose_name_plural = "Taken"

    objects = models.Manager()      # for the editor only


def taken_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen taken die afgerond en een deadline meer dan 3 kwartalen geleden.
    """

    now = timezone.now()
    oud = now - datetime.timedelta(days=92)

    aantal = 0
    for obj in (Taak
                .objects
                .filter(is_afgerond=True,
                        deadline__lt=oud)):
        aantal += 1
        obj.delete()
    # for

    if aantal > 0:
        stdout.write('[INFO] Aantal oude afgehandelde taken verwijderd: %s' % aantal)

# end of file
