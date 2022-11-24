# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from decimal import Decimal


THUMB_SIZE = (96, 96)

KEUZE_STATUS_RESERVERING_MANDJE = 'M'        # in mandje; moet nog omgezet worden in een bestelling
KEUZE_STATUS_RESERVERING_BESTELD = 'B'       # besteld; moet nog betaald worden
KEUZE_STATUS_BACKOFFICE = 'BO'               # betaling voldaan; ligt bij backoffice voor afhandeling
# FUTURE: KEUZE_STATUS_VERSTUURD        # afgehandeld door backoffice en verstuurd
# FUTURE: track en trace code voor in de mail naar koper


KEUZE_STATUS_CHOICES = (
    (KEUZE_STATUS_RESERVERING_MANDJE, "Reservering"),
    (KEUZE_STATUS_RESERVERING_BESTELD, "Besteld"),
    (KEUZE_STATUS_BACKOFFICE, "Betaald")
)

KEUZE_STATUS_TO_STR = {
    KEUZE_STATUS_RESERVERING_MANDJE: 'Gereserveerd, in mandje',
    KEUZE_STATUS_RESERVERING_BESTELD: 'Gereserveerd, wacht op betaling',
    KEUZE_STATUS_BACKOFFICE: 'Betaald; doorgegeven aan backoffice voor afhandeling'
}

KEUZE_STATUS_TO_SHORT_STR = {
    KEUZE_STATUS_RESERVERING_MANDJE: 'In mandje',
    KEUZE_STATUS_RESERVERING_BESTELD: 'Besteld',
    KEUZE_STATUS_BACKOFFICE: 'Betaald'
}


VERZENDKOSTEN_PAKKETPOST = "pak"
VERZENDKOSTEN_BRIEFPOST = "brief"       # max 5 lang

VERZENDKOSTEN_CHOICES = (
    (VERZENDKOSTEN_PAKKETPOST, "Pakketpost"),
    (VERZENDKOSTEN_BRIEFPOST, "Briefpost"),
)


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

    # de prijs voor dit product
    prijs_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))        # max 9999,99

    # wordt dit product gemaakt als het besteld wordt?
    onbeperkte_voorraad = models.BooleanField(default=False)

    # hoeveel producten mogen er nog verkocht worden?
    # TODO: commando maken om met N te verhogen (zonder race met nieuwe verkopen)
    aantal_op_voorraad = models.PositiveSmallIntegerField(default=0)

    # hoeveel kunnen er besteld worden?
    # (programmeerbaar)
    bestel_begrenzing = models.CharField(max_length=100, default='1', help_text='1-10,20,25,30,50', blank=True)

    # verzendkosten
    type_verzendkosten = models.CharField(max_length=5, default=VERZENDKOSTEN_PAKKETPOST, choices=VERZENDKOSTEN_CHOICES)

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "[%s] %s" % (self.pk, self.omslag_titel)

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

    # wie is de koper?
    # (BestelProduct verwijst naar dit record)
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)   # TODO: Bestelling heeft koper, dus waarom hier ook?

    # om welk product gaat het
    product = models.ForeignKey(WebwinkelProduct, on_delete=models.PROTECT)

    # aantal producten wat gekozen is
    aantal = models.PositiveSmallIntegerField(default=1)

    # TODO: ondersteun kortingen

    # hoeveel moet er betaald worden voor het aantal gekozen producten?
    totaal_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))       # max 9999,99

    # hoeveel is ontvangen?         # TODO: waarom tracken we dit hier? Dit hoort bij Betalen
    # (wordt ingevuld als de bestelling volledig betaald is)
    ontvangen_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))    # max 9999,99

    # log van bestelling, betalingen en eventuele wijzigingen
    log = models.TextField(blank=True)

    def korte_beschrijving(self):
        return "%s x %s" % (self.aantal, self.product.omslag_titel)

    def __str__(self):
        return self.korte_beschrijving()

# end of file
