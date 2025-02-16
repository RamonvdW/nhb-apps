# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from decimal import Decimal


class BestellingRegel(models.Model):
    """
        Regel van een bestelling
        Kan zijn: product of transportkosten

        Deze kan in het Mandje liggen of onderdeel zijn van een Bestelling
    """

    # korte beschrijving
    korte_beschrijving = models.CharField(max_length=250, default='?', blank=True)

    # BTW percentage van toepassing op deze regel
    # leeg = vrijgesteld van BTW
    btw_percentage = models.CharField(max_length=5, default='', blank=True)         # 21,00

    # prijs van deze regel (een positief bedrag)
    # de korting is hier nog niet vanaf
    prijs_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # de korting op deze regel (ook een positief bedrag!)
    korting_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    # het BTW bedrag voor deze regel
    # let op: is al inclusief in de prijs, dus niet optellen bij het totaal
    btw_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # code voor routing naar de juiste plugin
    # "wedstrijd"
    # "webwinkel"
    # "transport"
    # "evenement"
    # "opleiding"
    code = models.CharField(max_length=10, default='?', blank=True)

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = self.korte_beschrijving[:60]
        if len(self.korte_beschrijving) > 60:
            msg += '..'
        return "[%s] %s %s" % (self.pk, self.code, msg)

    class Meta:
        verbose_name = "Bestelling regel"


# end of file
