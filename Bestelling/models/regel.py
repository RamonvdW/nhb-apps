# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from decimal import Decimal


class BestellingRegel(models.Model):
    """
        Regel van een bestelling
        Kan zijn: product, korting of transportkosten

        Deze kan in het Mandje liggen of onderdeel zijn van een Bestelling
    """

    # korte beschrijving
    # als regel-break wordt BESTELLING_KORT_BREAK gebruikt
    korte_beschrijving = models.CharField(max_length=250, default='?', blank=True)

    # alleen voor kortingen: alle redenen voor de korting, gescheiden door een dubbel pipeline teken
    korting_redenen = models.CharField(max_length=500, default='', blank=True)

    # bedrag van deze regel
    # product: positief bedrag
    # korting: negatief bedrag
    bedrag_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # BTW percentage van toepassing op deze regel
    # leeg = vrijgesteld van BTW
    btw_percentage = models.CharField(max_length=5, default='', blank=True)         # 21,1

    # het BTW bedrag voor deze regel
    # let op: is al inclusief in de prijs, dus niet optellen bij het totaal
    btw_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # gewicht, voor keuze juiste verzendkosten pakket
    gewicht_gram = models.SmallIntegerField(default=0)

    # code voor routing naar de juiste plugin
    code = models.CharField(max_length=25, default='?', blank=True)

    def is_webwinkel(self):
        return self.code == BESTELLING_REGEL_CODE_WEBWINKEL

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = self.korte_beschrijving[:60]
        if len(self.korte_beschrijving) > 60:
            msg += '..'
        return "[%s] %s %s" % (self.pk, self.code, msg)

    class Meta:
        verbose_name = "Bestelling regel"


# end of file
