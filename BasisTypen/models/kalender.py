# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import ORGANISATIES, ORGANISATIE_WA
from .boogtype import BoogType
from .leeftijdsklasse import Leeftijdsklasse


class KalenderWedstrijdklasse(models.Model):

    """ definitie van de wedstrijdklassen voor de wedstrijden voor op de kalender (niet competitie) """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # klassen die verouderd zijn krijgen worden op deze manier eruit gehaald
    # zonder dat referenties die nog in gebruik zijn kapot gaan
    buiten_gebruik = models.BooleanField(default=False)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren
    beschrijving = models.CharField(max_length=80)

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # de leeftijdsklassen: mannen/vrouwen en aspirant, cadet, junior, senior, master, veteraan
    leeftijdsklasse = models.ForeignKey(Leeftijdsklasse, on_delete=models.PROTECT)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    volgorde = models.PositiveIntegerField()

    # officiële (internationale) afkorting voor deze wedstrijdklasse
    afkorting = models.CharField(max_length=10, default='?')

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Kalender Wedstrijdklasse"
        verbose_name_plural = "Kalender Wedstrijdklassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


# end of file
