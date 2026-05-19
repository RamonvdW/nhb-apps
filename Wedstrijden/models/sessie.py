# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import KalenderWedstrijdklasse


class WedstrijdSessie(models.Model):
    """ Een sessie van een wedstrijd """

    # op welke datum is deze sessie?
    datum = models.DateField()

    # hoe laat is deze sessie, hoe laat moet je aanwezig zijn, de geschatte eindtijd
    tijd_begin = models.TimeField()
    tijd_einde = models.TimeField()

    # beschrijving
    beschrijving = models.CharField(max_length=50, default='',
                                    blank=True)     # mag leeg zijn

    # toegestane wedstrijdklassen
    wedstrijdklassen = models.ManyToManyField(KalenderWedstrijdklasse, blank=True)

    # maximum aantal deelnemers
    max_sporters = models.PositiveSmallIntegerField(default=1)

    # het aantal inschrijvingen: de som van reserveringen en betaalde deelnemers
    aantal_inschrijvingen = models.PositiveSmallIntegerField(default=0)

    # inschrijvingen: zie WedstrijdInschrijving

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        msg = "(pk=%s) %s %s (%s plekken)" % (self.pk, self.datum, self.tijd_begin, self.max_sporters)
        if self.beschrijving:
            msg += ' ' + self.beschrijving
        return msg

    class Meta:
        verbose_name = "Wedstrijd sessie"
        verbose_name_plural = "Wedstrijd sessies"

    objects = models.Manager()      # for the editor only


# end of file
