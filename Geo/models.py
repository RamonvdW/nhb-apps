# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Geo.definities import CLUSTER_GEBRUIK_CHOICES, CLUSTER_GEBRUIK2STR


class Rayon(models.Model):
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
        verbose_name = "Rayon"

    objects = models.Manager()      # for the editor only


class Regio(models.Model):
    """ Tabel waarin de Regio definities """

    # 3-cijferige nummer van deze regio
    regio_nr = models.PositiveIntegerField(primary_key=True)

    # is dit een administratieve regio die niet mee doet voor de wedstrijden / competities?
    is_administratief = models.BooleanField(default=False)

    # beschrijving van de regio
    naam = models.CharField(max_length=50)

    # kopie rayon.rayon_nr
    rayon_nr = models.PositiveIntegerField(default=0)

    # rayon waar deze regio bij hoort
    rayon = models.ForeignKey(Rayon, on_delete=models.PROTECT)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Regio"
        verbose_name_plural = "Regio's"

    objects = models.Manager()      # for the source code editor only


class Cluster(models.Model):
    """ Tabel waarin de definitie van een cluster staat """

    # regio waar dit cluster bij hoort
    regio = models.ForeignKey(Regio, on_delete=models.PROTECT)

    # letter voor unieke identificatie van het cluster
    letter = models.CharField(max_length=1, default='x')

    # beschrijving het cluster
    naam = models.CharField(max_length=50, default='', blank=True)

    # aparte clusters voor 18m en 25m
    gebruik = models.CharField(max_length=2, choices=CLUSTER_GEBRUIK_CHOICES)

    def cluster_code(self):
        return "%s%s" % (self.regio.regio_nr, self.letter)

    def cluster_code_str(self):
        msg = "%s voor " % self.cluster_code()
        try:
            msg += CLUSTER_GEBRUIK2STR[self.gebruik]
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
        verbose_name = "Cluster"

        # zorg dat elk cluster uniek is
        unique_together = ('regio', 'letter')

    objects = models.Manager()      # for the source code editor only


# end of file
