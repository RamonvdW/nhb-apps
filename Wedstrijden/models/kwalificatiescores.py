# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Wedstrijden.definities import KWALIFICATIE_CHECK_CHOICES, KWALIFICATIE_CHECK_NOG_DOEN
from .inschrijving import WedstrijdInschrijving


class Kwalificatiescore(models.Model):

    # voor welke inschrijving is dit?
    inschrijving = models.ForeignKey(WedstrijdInschrijving, on_delete=models.CASCADE)

    # wanneer was de wedstrijd
    datum = models.DateField(default='2000-01-01')

    # naam van de wedstrijd
    naam = models.CharField(max_length=50)

    # locatie van de wedstrijd (plaats + land)
    waar = models.CharField(max_length=50)

    # behaald resultaat
    resultaat = models.PositiveSmallIntegerField(default=0)

    # link naar de uitslag
    uitslag = models.CharField(max_length=250, default='', blank=True)

    # controle status
    check_status = models.CharField(max_length=1, default=KWALIFICATIE_CHECK_NOG_DOEN,
                                    choices=KWALIFICATIE_CHECK_CHOICES)

    log = models.TextField(default='')

    def __str__(self):
        return "[%s] %s: %s (%s)" % (self.datum, self.resultaat, self.naam, self.waar)

    objects = models.Manager()      # for the editor only


# end of file
