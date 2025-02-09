# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Bestelling.definities import BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_OPTIES
from Bestelling.models.product_obsolete import BestellingProduct
from Bestelling.models.regel import BestellingRegel
from decimal import Decimal


class BestellingMandje(models.Model):

    """ Een verzameling producten die nog veranderd kunnen worden en waaraan een korting gekoppeld kan worden.
        Wordt omgezet in een Bestelling zodra 'afrekenen' wordt gekozen.
    """

    # van wie is dit mandje?
    # maximaal 1 mandje per account
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    # de gekozen producten met prijs en korting
    producten = models.ManyToManyField(BestellingProduct)
    regels = models.ManyToManyField(BestellingRegel)

    # afleveradres: automatisch voor leden, handmatig voor gastaccounts (kan ook buitenlands adres zijn)
    # (gebaseerd op info van https://docs.superoffice.com/nl/company/learn/address-formats.html)
    afleveradres_regel_1 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_2 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_3 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_4 = models.CharField(max_length=100, default='', blank=True)      # postcode + plaats
    afleveradres_regel_5 = models.CharField(max_length=100, default='', blank=True)      # land

    # verzendkosten
    transport = models.CharField(max_length=1, default=BESTELLING_TRANSPORT_NVT, choices=BESTELLING_TRANSPORT_OPTIES)
    verzendkosten_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))    # max 9999,99

    # belasting in verschillende categorieën: leeg = niet gebruikt
    btw_percentage_cat1 = models.CharField(max_length=5, default='', blank=True)         # 21,00
    btw_percentage_cat2 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat3 = models.CharField(max_length=5, default='', blank=True)

    # het aantal van het totaal voor elk van de BTW percentages
    # (dus niet optellen bij het totaal!)
    btw_euro_cat1 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat2 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat3 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))           # max 99999,99

    # maximaal 1x per dag mag een e-mail herinnering verstuurd worden als er nog producten in het mandje liggen
    vorige_herinnering = models.DateField(default='2000-01-01')

    def bepaal_totaalprijs_opnieuw(self):
        """ Bepaal het totaal_euro veld opnieuw, gebaseerd op alles wat in het mandje ligt

            Let op: Roep deze aan met een select_for_update() lock
        """
        self.totaal_euro = Decimal(0)
        for product in self.producten.all():
            self.totaal_euro += product.prijs_euro
            self.totaal_euro -= product.korting_euro
        # for
        self.totaal_euro += self.verzendkosten_euro
        self.save(update_fields=['totaal_euro'])

    def __str__(self):
        """ beschrijving voor de admin interface """
        return self.account.username

    class Meta:
        verbose_name = "Mandje"
        verbose_name_plural = "Mandjes"


# end of file
