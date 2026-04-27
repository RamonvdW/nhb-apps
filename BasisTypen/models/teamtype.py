# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import ORGANISATIES, ORGANISATIE_WA
from .boogtype import BoogType


class TeamType(models.Model):
    """ team type: voor gebruik in de team competities """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # R/R2/C/BB/BB2/IB/TR/LB
    afkorting = models.CharField(max_length=3)

    # Recurve team, etc.
    beschrijving = models.CharField(max_length=50)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.PositiveSmallIntegerField(default=0)

    # toegestane boogtypen
    boog_typen = models.ManyToManyField(BoogType)

    # is dit team type nog actueel?
    # zolang in gebruik blijft een teamtype bestaan
    # True = niet meer gebruiken voor nieuwe wedstrijden
    buiten_gebruik = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team type"
        verbose_name_plural = "Team typen"

        ordering = ['volgorde']

        indexes = [
            # help vinden op afkorting
            models.Index(fields=['afkorting']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),

            # FUTURE: extra index voor organisatie, in combinatie met afkorting/volgorde??
        ]

    objects = models.Manager()      # for the editor only


# end of file
