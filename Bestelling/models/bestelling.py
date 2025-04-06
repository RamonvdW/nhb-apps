# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from Bestelling.definities import (BESTELLING_STATUS_CHOICES, BESTELLING_STATUS_NIEUW, BESTELLING_STATUS2STR,
                                   BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_OPTIES)
from Bestelling.models.regel import BestellingRegel
from Betaal.format import format_bedrag_euro
from Betaal.models import BetaalActief, BetaalTransactie, BetaalMutatie, BetaalInstellingenVereniging
from decimal import Decimal


class Bestelling(models.Model):

    """ een volledige bestelling die afgerekend kan worden / afgerekend is """

    # het unieke bestelnummer
    bestel_nr = models.PositiveIntegerField()

    # wanneer aangemaakt?
    # hiermee kunnen onbetaalde bestellingen na een tijdje opgeruimd worden
    aangemaakt = models.DateTimeField(auto_now_add=True)

    # van wie is deze bestelling
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # welke vereniging is ontvanger van de gelden voor deze bestelling?
    # per bestelling kan er maar 1 ontvanger zijn
    ontvanger = models.ForeignKey(BetaalInstellingenVereniging, on_delete=models.PROTECT,
                                  null=True, blank=True)        # alleen nodig voor migratie

    # verplichte informatie over de verkoper
    # naam, adres, kvk, email, telefoon
    verkoper_naam = models.CharField(max_length=100, default='', blank=True)
    verkoper_adres1 = models.CharField(max_length=100, default='', blank=True)      # straat
    verkoper_adres2 = models.CharField(max_length=100, default='', blank=True)      # postcode, plaats
    verkoper_kvk = models.CharField(max_length=15, default='', blank=True)
    verkoper_btw_nr = models.CharField(max_length=15, default='', blank=True)
    verkoper_email = models.EmailField(default='', blank=True)
    verkoper_telefoon = models.CharField(max_length=20, default='', blank=True)

    # bankrekening details
    verkoper_iban = models.CharField(max_length=18, default='', blank=True)
    verkoper_bic = models.CharField(max_length=11, default='', blank=True)          # 8 of 11 tekens
    verkoper_heeft_mollie = models.BooleanField(default=False)

    # de bestelde producten met prijs en korting
    regels = models.ManyToManyField(BestellingRegel)

    # afleveradres: automatisch voor leden, handmatig voor gastaccounts (kan ook buitenlands adres zijn)
    # (gebaseerd op info van https://docs.superoffice.com/nl/company/learn/address-formats.html)
    afleveradres_regel_1 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_2 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_3 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_4 = models.CharField(max_length=100, default='', blank=True)      # postcode + plaats
    afleveradres_regel_5 = models.CharField(max_length=100, default='', blank=True)      # land

    # transport (verzenden of ophalen)
    # bedrag staat in een BestellingRegel
    transport = models.CharField(max_length=1, default=BESTELLING_TRANSPORT_NVT, choices=BESTELLING_TRANSPORT_OPTIES)

    # belasting in verschillende categorieën: leeg = niet gebruikt
    # btw percentage, zonder het % teken: 21 / 20,5
    btw_percentage_cat1 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat2 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat3 = models.CharField(max_length=5, default='', blank=True)

    btw_euro_cat1 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat2 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat3 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))       # max 99999,99

    # de status van de hele bestelling
    status = models.CharField(max_length=1, default=BESTELLING_STATUS_NIEUW, choices=BESTELLING_STATUS_CHOICES)

    # de opgestarte betaling/restitutie wordt hier bijgehouden
    # de BetaalMutatie wordt opgeslagen zodat deze is aangemaakt. Daarin zet de achtergrond taak een payment_id.
    # daarmee kunnen we het BetaalActief record vinden met de status van de betaling en de log
    betaal_mutatie = models.ForeignKey(BetaalMutatie, on_delete=models.SET_NULL, null=True, blank=True)
    betaal_actief = models.ForeignKey(BetaalActief, on_delete=models.SET_NULL, null=True, blank=True)

    # de afgeronde betalingen: ontvangst en restitutie
    transacties = models.ManyToManyField(BetaalTransactie, blank=True)

    # logboek van hoeveel en wanneer er ontvangen en terugbetaald is
    log = models.TextField()

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "%s" % self.bestel_nr
        msg += " %s" % BESTELLING_STATUS2STR[self.status]
        msg += " [%s]" % timezone.localtime(self.aangemaakt).strftime('%Y-%m-%d %H:%M:%S')
        msg += " koper=%s" % self.account.username
        msg += " " + format_bedrag_euro(self.totaal_euro)

        return msg

    def mh_bestel_nr(self):
        return "MH-%s" % self.bestel_nr

    class Meta:
        verbose_name = "Bestelling"
        verbose_name_plural = "Bestellingen"


# end of file
