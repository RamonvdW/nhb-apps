# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Bestelling.models import BestellingRegel
from Webwinkel.definities import (VERZENDKOSTEN_CHOICES, VERZENDKOSTEN_PAKKETPOST,
                                  KEUZE_STATUS_CHOICES, KEUZE_STATUS_RESERVERING_MANDJE)
from decimal import Decimal


class WebwinkelFoto(models.Model):
    """ Een foto van een product.
    """

    # locatie van het plaatje op het filesysteem onder settings.FOTOBANK_PATH
    locatie = models.CharField(max_length=100, blank=True)

    # locatie van de thumbnail van dit plaatje
    locatie_thumb = models.CharField(max_length=100, blank=True)

    # in welke volgorde moet deze foto getoond worden
    volgorde = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "%s: %s" % (self.volgorde, self.locatie)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Webwinkel foto"
        verbose_name_plural = "Webwinkel foto's"
        ordering = ('locatie', 'volgorde')


class WebwinkelProduct(models.Model):
    """ Een product in de webwinkel """

    # mag het product getoond worden?
    # hiermee kan een product "uit het schap" gehaald worden
    # terwijl er toch nog verwijzingen naar blijven bestaan vanuit de bestellingen
    mag_tonen = models.BooleanField(default=True)

    # in welke volgorde moet dit product getoond worden
    volgorde = models.PositiveSmallIntegerField(default=9999)

    # onder welke sectie wordt deze gegroepeerd op de voorpagina
    sectie = models.CharField(max_length=50, default='', blank=True)

    # subtitel is alleen van toepassing op het eerste product in die sectie (met de laagste volgorde)
    sectie_subtitel = models.CharField(max_length=250, default='', blank=True)

    # de titel voor op de omslag
    omslag_titel = models.CharField(max_length=25, default='', blank=True)

    # de foto voor het overzicht
    omslag_foto = models.ForeignKey(WebwinkelFoto, on_delete=models.SET_NULL, related_name='omslagfoto',
                                    null=True, blank=True)      # mag leeg zijn

    # de lange beschrijving
    beschrijving = models.TextField(default='', blank=True)

    # de grote foto's van dit product
    fotos = models.ManyToManyField(WebwinkelFoto, blank=True)

    # hoeveel eenheden bevat dit product
    # voorbeeld: doos met 6 mokken
    bevat_aantal = models.PositiveSmallIntegerField(default=1)

    # toevoeging voor de aantallen te bestellen, bijvoorbeeld "6 dozen" or "3 containers"
    # enkelvoud/meervoud moet met een komma gescheiden worden
    # bij leeg wordt "stuks" gebruikt
    eenheid = models.CharField(max_length=50, default='', blank=True)

    # maat (alleen voor kleding)
    # voorbeeld: XL
    kleding_maat = models.CharField(max_length=10, default='', blank=True)

    # de prijs voor dit product
    prijs_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))        # max 9999,99

    # wordt dit product gemaakt als het besteld wordt?
    onbeperkte_voorraad = models.BooleanField(default=False)

    # hoeveel producten mogen er nog verkocht worden?
    # FUTURE: commando maken om met N te verhogen (zonder race met nieuwe verkopen)
    aantal_op_voorraad = models.PositiveSmallIntegerField(default=0)

    # hoeveel kunnen er besteld worden?
    # (programmeerbaar)
    bestel_begrenzing = models.CharField(max_length=100, default='1', help_text='1-10,20,25,30,50', blank=True)

    # gewicht, voor keuze juiste verzendkosten pakket
    gewicht_gram = models.SmallIntegerField(default=0)

    # verzendkosten
    type_verzendkosten = models.CharField(max_length=5, default=VERZENDKOSTEN_PAKKETPOST, choices=VERZENDKOSTEN_CHOICES)

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        msg = "[%s] %s" % (self.volgorde, self.omslag_titel)
        if self.kleding_maat:
            msg += ' (maat %s)' % self.kleding_maat
        return msg

    class Meta:
        verbose_name = "Webwinkel product"
        verbose_name_plural = "Webwinkel producten"


class WebwinkelKeuze(models.Model):
    """ Een type product uit de webwinkel gekozen voor in het mandje en later bestelling """

    # wanneer is dit record aangemaakt?
    wanneer = models.DateTimeField()

    # status van deze keuze: in het mandje, bestelling, betaald
    status = models.CharField(max_length=2, choices=KEUZE_STATUS_CHOICES,
                              default=KEUZE_STATUS_RESERVERING_MANDJE)

    # koppeling aan de bestelling
    bestelling = models.ForeignKey(BestellingRegel, on_delete=models.PROTECT, null=True)

    # om welk product gaat het
    product = models.ForeignKey(WebwinkelProduct, on_delete=models.PROTECT)

    # aantal producten wat gekozen is
    aantal = models.PositiveSmallIntegerField(default=1)

    # log van bestelling, betalingen en eventuele wijzigingen
    log = models.TextField(blank=True)

    def korte_beschrijving(self):
        kort = "%s x %s" % (self.aantal, self.product.omslag_titel)
        if self.product.kleding_maat:
            kort += ' maat %s' % self.product.kleding_maat
        return kort

    def __str__(self):
        return self.korte_beschrijving()

# end of file
