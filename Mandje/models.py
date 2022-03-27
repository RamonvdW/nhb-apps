# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Kalender.models import KalenderInschrijving


class MandjeInhoud(models.Model):

    # bij wie liggen deze items in het mandje?
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # inschrijving voor een wedstrijd
    inschrijving = models.ForeignKey(KalenderInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # prijs van deze regel
    # als een kortingscode toegepast is, dan is deze prijs al verlaagd
    prijs_euro = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)     # max 999,99

    class Meta:
        verbose_name_plural = verbose_name = "Mandje inhoud"


class MandjeTransactie(models.Model):

    """ Compleet logboek van aankopen en terug betalingen """

    # wanneer uitgevoerd?
    wanneer = models.DateTimeField()

    # bedrag
    euros = models.DecimalField(max_digits=7, decimal_places=2)     # max=99999,99

    # wie heeft het bedrag gestuurd
    zender = models.CharField(max_length=200)

    # wie is de ontvanger van het bedrag?
    ontvanger = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Mandje transactie"


# end of file
