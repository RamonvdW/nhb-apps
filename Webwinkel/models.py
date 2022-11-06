# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.templatetags.static import static
from decimal import Decimal


THUMB_SIZE = (96, 96)


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

    def get_static_url(self):
        return static("webwinkel_fotos/" + self.locatie)

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
    eenheid = models.CharField(max_length=50, default='', blank=True)

    # de prijs voor dit product
    prijs_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))     # max 9999,99

    # wordt dit product gemaakt als het besteld wordt?
    onbeperkte_voorraad = models.BooleanField(default=False)

    # hoeveel producten mogen er nog verkocht worden?
    aantal_op_voorraad = models.PositiveSmallIntegerField(default=0)

    # hoeveel kunnen er besteld worden?
    # (programmeerbaar)
    bestel_begrenzing = models.CharField(max_length=100, default='1', help_text='1-10,20,25,30,50', blank=True)

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "[%s] %s" % (self.pk, self.omslag_titel)

    class Meta:
        verbose_name = "Webwinkel product"
        verbose_name_plural = "Webwinkel producten"


# end of file
