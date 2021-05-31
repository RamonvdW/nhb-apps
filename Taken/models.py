# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from Competitie.models import DeelCompetitie
import datetime


class Taak(models.Model):

    """ Bijhouden van een specifieke taak """

    # is de taak afgehandeld / klaar, of nog niet?
    is_afgerond = models.BooleanField(default=False)

    # wie moet actie ondernemen / bij wie op de takenlijst zetten
    toegekend_aan = models.ForeignKey(Account, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='account_taken_toegekend')

    # wanneer moet het af zijn?
    deadline = models.DateField()

    # wie heeft hier om gevraagd
    aangemaakt_door = models.ForeignKey(Account, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='account_taken_aangemaakt')

    # beschrijving van de uit te voeren taak
    beschrijving = models.TextField(max_length=1000)

    # langere uitleg in de handleiding
    handleiding_pagina = models.CharField(max_length=75, blank=True)

    # geschiedenis van deze taak
    log = models.TextField(max_length=50000, blank=True)

    # hoort deze bij een deel van de competitie? (Regio/RK/BK)
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE,
                                       null=True, blank=True)

    def __str__(self):
        msg = str(self.pk)
        if self.is_afgerond:
            msg += " (afgerond)"
        msg += " [%s] %s" % (self.toegekend_aan, self.beschrijving[:200])
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Taak"
        verbose_name_plural = "Taken"

    objects = models.Manager()      # for the editor only


def taken_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen taken die ...
    """

    # TODO: implement

    now = timezone.now()
    # max_age = now - datetime.timedelta(days=)

    # for obj in (Taken
    #            .objects
    #            .filter(...)):
    #
    #    stdout.write('[INFO] Verwijder ongebruikte tijdelijke url %s' % obj)
    #    obj.delete()
    # for


# end of file
