# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Geo.models import Regio, Cluster


class Vereniging(models.Model):
    """ Tabel waarin gegevens van de Verenigingen staan """

    # 4-cijferige nummer van de vereniging
    ver_nr = models.PositiveIntegerField(primary_key=True)

    # naam van de vereniging
    naam = models.CharField(max_length=50)

    # adres van "het bedrijf"
    adres_regel1 = models.CharField(max_length=50, default='', blank=True)
    adres_regel2 = models.CharField(max_length=50, default='', blank=True)

    # locatie van het doel van de vereniging
    plaats = models.CharField(max_length=35, blank=True)

    # de regio waarin de vereniging zit
    regio = models.ForeignKey(Regio, on_delete=models.PROTECT)

    # de optionele clusters waar deze vereniging bij hoort
    clusters = models.ManyToManyField(Cluster,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # er is een vereniging voor persoonlijk lidmaatschap
    # deze leden mogen geen wedstrijden schieten
    geen_wedstrijden = models.BooleanField(default=False)

    # is dit deze vereniging voor gast-accounts?
    is_extern = models.BooleanField(default=False)

    # KvK-nummer - wordt gebruikt bij verkoop wedstrijd/opleiding
    kvk_nummer = models.CharField(max_length=15, default='', blank=True)

    # website van deze vereniging
    website = models.CharField(max_length=100, default='', blank=True)

    # algemeen e-mailadres
    contact_email = models.EmailField(blank=True)

    # telefoonnummer van deze vereniging
    # maximum is 15 tekens, maar we staan streepjes/spaties toe
    telefoonnummer = models.CharField(max_length=20, default='', blank=True)

    # bankrekening details
    bank_iban = models.CharField(max_length=18, default='', blank=True)
    bank_bic = models.CharField(max_length=11, default='', blank=True)      # 8 of 11 tekens

    def ver_nr_en_naam(self):
        return "[%s] %s" % (self.ver_nr, self.naam)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.ver_nr_en_naam()

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Vereniging"
        verbose_name_plural = "Verenigingen"

    objects = models.Manager()      # for the editor only


# end of file
