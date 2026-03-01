# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.models import CompetitieIndivKlasse
from .kampioenschap import KampBK


class CutBK(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal deelnemers in een wedstrijdklasse.
        De BKO kan dit bijstellen specifiek voor zijn BK.
    """

    # voor welk kampioenschap
    kamp = models.ForeignKey(KampBK, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse, on_delete=models.CASCADE)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s - %s: %s" % (self.kamp, self.indiv_klasse.beschrijving, self.limiet)

    class Meta:
        verbose_name = "Cut BK"
        verbose_name_plural = "Cuts BK"


# end of file
