# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Sporter.models import Sporter
from Vereniging.models import Vereniging


class Secretaris(models.Model):

    """ de secretaris van een vereniging, volgens het CRM
        (een vereniging kan meerdere secretarissen hebben)

        Let op: Secretaris bestaat ook als er beheerder nog geen account aangemaakt heeft
                Functie is voor de uitvoer: is gekoppeld aan bestaande accounts
                Functie wordt bij inlog aangepast aan de hand van Secretaris

        deze aparte tabel voorkomt een circulaire afhankelijkheid tussen Sporter (lid bij vereniging)
        en de secretaris van een vereniging (is een sporter)
    """

    # van welke vereniging
    vereniging = models.ForeignKey(Vereniging, on_delete=models.CASCADE)

    # de leden die secretaris zijn (typisch maar een)
    sporters = models.ManyToManyField(Sporter, blank=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Secretaris Vereniging"

    def __str__(self):
        return "[%s] %s: %s" % (self.vereniging.ver_nr, self.vereniging.naam,
                                " + ".join([sporter.lid_nr_en_volledige_naam() for sporter in self.sporters.all()]))


# end of file
