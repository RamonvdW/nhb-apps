# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from Bestelling.definities import BESTELLING_MUTATIE_TO_STR, BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_OPTIES
from Bestelling.models import Bestelling, BestellingRegel
from Sporter.models import SporterBoog
from Wedstrijden.models import WedstrijdSessie, KalenderWedstrijdklasse
from decimal import Decimal


class BestellingHoogsteBestelNr(models.Model):

    """ een kleine tabel om het hoogst gebruikte bestelnummer bij te houden """

    # hoogste gebruikte boekingsnummer
    hoogste_gebruikte_bestel_nr = models.PositiveIntegerField(default=0)


class BestellingMutatie(models.Model):

    """ Deze tabel voedt de achtergrondtaak die de interactie met het mandje en bestellingen doet """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie BESTEL_MUTATIE_*)
    code = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN      account(=mandje), product_pk
    # BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN:     account(=mandje), product_pk
    # BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN:     account(=mandje), product_pk
    # BESTELLING_MUTATIE_WEBWINKEL_KEUZE            account(=mandje), product_pk
    # BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN:        product_pk
    # BESTELLING_MUTATIE_OPLEIDING_AFMELDEN:        product_pk
    # BESTELLING_MUTATIE_WEDSTRIJD_AANPASSEN:   account, product_pk, sporterboog, sessie, wedstrijdklasse

    # BESTELLING_MUTATIE_VERWIJDER:                 account(=mandje), regel
    # BESTELLING_MUTATIE_MAAK_BESTELLING:           account(=mandje)
    # BESTELLING_MUTATIE_BETALING_AFGEROND:         bestelling, betaling_is_gelukt
    # BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN:     bestelling, bedrag_euro
    # BESTELLING_MUTATIE_ANNULEER:                  bestelling
    # BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD:
    # BESTELLING_MUTATIE_TRANSPORT:                 account(=mandje), transport

    # mandje van dit account
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    # anonieme verwijzing naar een product: evenement, opleiding, webwinkel keuze of wedstrijd
    product_pk = models.PositiveBigIntegerField(default=0)

    # het product waar deze mutatie betrekking op heeft
    regel = models.ForeignKey(BestellingRegel, on_delete=models.SET_NULL, null=True, blank=True)

    # gevraagde korting om toe te passen
    korting = models.CharField(max_length=20, default='', blank=True)

    # de bestelling waar deze mutatie betrekking op heeft
    bestelling = models.ForeignKey(Bestelling, on_delete=models.SET_NULL, null=True, blank=True)

    # status van de betaling: gelukt, of niet?
    betaling_is_gelukt = models.BooleanField(default=False)

    # het ontvangen of betaalde bedrag
    bedrag_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # nieuwe transport keuze
    transport = models.CharField(max_length=1, default=BESTELLING_TRANSPORT_NVT, choices=BESTELLING_TRANSPORT_OPTIES)

    # wedstrijd aanpassing
    sessie = models.ForeignKey(WedstrijdSessie, on_delete=models.SET_NULL, null=True, blank=True)
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.SET_NULL, null=True, blank=True)
    wedstrijdklasse = models.ForeignKey(KalenderWedstrijdklasse, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Bestelling mutatie"

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        msg = "[%s]" % timezone.localtime(self.when).strftime('%Y-%m-%d %H:%M:%S')
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.code, BESTELLING_MUTATIE_TO_STR[self.code])
        except KeyError:
            msg += " %s (???)" % self.code

        return msg


# end of file
