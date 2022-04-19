# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Betaal.models import BetaalTransactie
from Kalender.models import KalenderInschrijving
from decimal import Decimal


BESTEL_KORTINGSCODE_MINLENGTH = 8

BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK = 1


class BestelProduct(models.Model):

    """ Een product dat opgenomen kan worden in een bestelling en in een mandje geplaatst kan worden,
        eventueel met kortingscode.
    """

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
        if self.inschrijving:
            msg = str(self.inschrijving)
        else:
            # TODO: andere producten
            msg = '?'

        msg += ' %s' % self.prijs_euro
        if self.korting_euro > 0.0001:
            msg += ' -%s' % self.korting_euro

        return msg

    def korte_beschrijving(self):
        if self.inschrijving:
            return self.inschrijving.korte_beschrijving()
        return "?"

    class Meta:
        verbose_name = "Bestel product"
        verbose_name_plural = "Bestel producten"


class BestelMandje(models.Model):

    """ Een verzameling producten die nog veranderd kunnen worden en waaraan kortingscodes gekoppeld kunnen worden.
        Wordt omgezet in een Bestelling zodra 'afrekenen' wordt gekozen.
    """

    # van wie is dit mandje?
    # maximaal 1 mandje per account
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    # de gekozen producten met prijs en korting
    producten = models.ManyToManyField(BestelProduct)

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))       # max 99999,99

    def bepaal_totaalprijs_opnieuw(self):
        """ Bepaal het totaal_euro veld opnieuw, gebaseerd op alles wat in het mandje ligt

            Let op: Roep deze aan met een select_for_update() lock
        """
        self.totaal_euro = Decimal(0)
        for product in self.producten.all():
            self.totaal_euro += product.prijs_euro
            self.totaal_euro -= product.korting_euro
        # for
        self.save(update_fields=['totaal_euro'])

    def __str__(self):
        """ beschrijving voor de admin interface """
        return self.account.username

    class Meta:
        verbose_name = "Mandje"
        verbose_name_plural = "Mandjes"


class Bestelling(models.Model):

    """ een volledige bestelling die afgerekend kan worden / afgerekend is
    """

    # het unieke bestelnummer
    bestel_nr = models.PositiveIntegerField()

    # wanneer aangemaakt?
    # hiermee kunnen onbetaalde bestellingen na een tijdje opgeruimd worden
    aangemaakt = models.DateTimeField(auto_now=True)

    # van wie is deze bestelling
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # de bestelde producten met prijs en korting
    producten = models.ManyToManyField(BestelProduct)

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))       # max 99999,99

    # betalingen: ontvangst en restitutie
    transacties = models.ManyToManyField(BetaalTransactie)

    # logboek van hoeveel en wanneer er ontvangen en terugbetaald is
    log = models.TextField()

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "%s: " % self.bestel_nr
        msg += "%s " % self.account.username
        return msg

    class Meta:
        verbose_name = "Bestelling"
        verbose_name_plural = "Bestellingen"


class BestelHoogsteBestelNr(models.Model):

    """ een kleine tabel om het hoogst gebruikte bestelnummer bij te houden """

    # hoogste gebruikte boekingsnummer
    hoogste_gebruikte_bestel_nr = models.PositiveIntegerField(default=0)


# TODO: boekhouding: betaald bedrag, ingehouden transactiekosten door CPSP, ontvangen bedrag, uitbetaalde bedragen, opsplitsing btw/transactiekosten


# end of file
