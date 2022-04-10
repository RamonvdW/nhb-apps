# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Kalender.models import KalenderInschrijving
from decimal import Decimal


MINIMUM_CODE_LENGTH = 8
MANDJE_NOG_GEEN_BESTELLING = 0      # speciaal bestelnummer voor het mandje


class MandjeProduct(models.Model):

    # bij wie liggen deze items in het mandje?
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # inschrijving voor een wedstrijd
    inschrijving = models.ForeignKey(KalenderInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # FUTURE: andere mogelijke regels in dit mandje

    # prijs van deze regel (een positief bedrag)
    prijs_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # de korting op deze regel (ook een positief bedrag!)
    korting_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    # TODO: afmelding + gedeeltelijke terugstorting bijhouden

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "%s: " % self.account.username

        if self.inschrijving:
            msg += str(self.inschrijving)
        else:
            # TODO: andere producten
            msg += '?'

        msg += ' %s' % self.prijs_euro
        if self.korting_euro > 0.0001:
            msg += ' -%s' % self.korting_euro

        return msg

    class Meta:
        verbose_name = "Mandje product"
        verbose_name_plural = "Mandje producten"


class MandjeBestelling(models.Model):

    """ een volledige bestelling die afgerekend kan worden / afgerekend is """

    # het unieke boekingsnummer
    # wordt pas uitgenomen als er op "afrekenen" gedrukt wordt
    boekingsnummer = models.PositiveIntegerField(default=MANDJE_NOG_GEEN_BESTELLING)

    # wanneer aangemaakt?
    # hiermee kunnen onbetaalde bestellingen na een tijdje opgeruimd worden
    aangemaakt = models.DateTimeField(auto_now=True)

    # van wie is deze bestelling
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # de bestelde producten met prijs en korting
    producten = models.ManyToManyField(MandjeProduct)

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)      # max 99999,99

    # is deze betaald?
    is_betaald = models.BooleanField(default=False)

    # wanneer is deze betaald?
    wanneer_betaald = models.DateTimeField(default='2000-01-01T00:00:00+00:00')

    # TODO: transactie referentie toevoegen?

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "%s: " % self.boekingsnummer
        msg += "%s " % self.account.username
        return msg

    class Meta:
        verbose_name = "Mandje bestelling"
        verbose_name_plural = "Mandje bestellingen"


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


# TODO: boekhouding: betaald bedrag, ingehouden transactiekosten door CPSP, ontvangen bedrag, uitbetaalde bedragen, opsplitsing btw/transactiekosten


# end of file
