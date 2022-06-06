# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
import datetime


# global
maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID

GEBRUIK = [('18', 'Indoor'),
           ('25', '25m 1pijl')]

GEBRUIK2STR = {'18': 'Indoor',
               '25': '25m 1pijl'}


class NhbRayon(models.Model):
    """ Tabel waarin de Rayon definities """

    # 1-digit nummer van dit rayon
    rayon_nr = models.PositiveIntegerField(primary_key=True)

    # korte naam van het rayon (Rayon 1)
    naam = models.CharField(max_length=20)      # Rayon 3

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # geografisch gebied klopt niet helemaal en wordt nu niet meer getoond
        # return self.naam + ' ' + self.geografisch_gebied
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb rayon"
        verbose_name_plural = "Nhb rayons"

    objects = models.Manager()      # for the editor only


class NhbRegio(models.Model):
    """ Tabel waarin de Regio definities """

    # 3-cijferige NHB nummer van deze regio
    regio_nr = models.PositiveIntegerField(primary_key=True)

    # beschrijving van de regio
    naam = models.CharField(max_length=50)

    # rayon waar deze regio bij hoort
    rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT)

    # is dit een administratieve regio die niet mee doet voor de wedstrijden / competities?
    is_administratief = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb regio"
        verbose_name_plural = "Nhb regios"

    objects = models.Manager()      # for the source code editor only


class NhbCluster(models.Model):
    """ Tabel waarin de definitie van een cluster staat """

    # regio waar dit cluster bij hoort
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # letter voor unieke identificatie van het cluster
    letter = models.CharField(max_length=1, default='x')

    # beschrijving het cluster
    naam = models.CharField(max_length=50, default='', blank=True)

    # aparte clusters voor 18m en 25m
    gebruik = models.CharField(max_length=2, choices=GEBRUIK)

    def cluster_code(self):
        return "%s%s" % (self.regio.regio_nr, self.letter)

    def cluster_code_str(self):
        msg = "%s voor " % self.cluster_code()
        try:
            msg += GEBRUIK2STR[self.gebruik]
        except KeyError:         # pragma: no cover
            msg = "?"
        return msg

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = self.cluster_code_str()
        if self.naam:
            msg += " (%s)" % self.naam
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb cluster"
        verbose_name_plural = "Nhb clusters"

        # zorg dat elk cluster uniek is
        unique_together = ('regio', 'letter')

    objects = models.Manager()      # for the source code editor only


class NhbVereniging(models.Model):
    """ Tabel waarin gegevens van de Verenigingen van de NHB staan """

    # 4-cijferige nummer van de vereniging
    ver_nr = models.PositiveIntegerField(primary_key=True)

    # naam van de vereniging
    naam = models.CharField(max_length=200)

    # adres van "het bedrijf"
    adres_regel1 = models.CharField(max_length=100, default='', blank=True)
    adres_regel2 = models.CharField(max_length=100, default='', blank=True)

    # locatie van het doel van de vereniging
    plaats = models.CharField(max_length=100, blank=True)

    # de regio waarin de vereniging zit
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # de optionele clusters waar deze vereniging bij hoort
    clusters = models.ManyToManyField(NhbCluster,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # er is een vereniging voor persoonlijk lidmaatschap
    # deze leden mogen geen wedstrijden schieten
    geen_wedstrijden = models.BooleanField(default=False)

    # KvK nummer - wordt gebruikt bij verkoop wedstrijd/opleiding
    kvk_nummer = models.CharField(max_length=15, default='', blank=True)

    # website van deze vereniging
    website = models.CharField(max_length=100, default='', blank=True)

    # algemeen e-mailadres
    contact_email = models.EmailField(blank=True)

    # telefoonnummer van deze vereniging
    # maximum is 15 tekens, maar we staan streepjes/spaties toe
    telefoonnummer = models.CharField(max_length=20, default='', blank=True)

    def ver_nr_en_naam(self):
        return "[%s] %s" % (self.ver_nr, self.naam)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.ver_nr_en_naam()

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb vereniging"
        verbose_name_plural = "Nhb verenigingen"

    objects = models.Manager()      # for the editor only


# end of file
