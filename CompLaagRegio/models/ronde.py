# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.models.competitie import CompetitieMatch
from Geo.models import Cluster
from .regiocomp import RegioComp


class RegioRonde(models.Model):

    """ Definitie van een competitieronde """

    # bij welke regiocompetitie hoort deze (geeft 18m / 25m) + regio_nr + functie + is_afgesloten
    regiocomp = models.ForeignKey(RegioComp, on_delete=models.CASCADE)

    # het cluster waar deze planning specifiek bij hoort (optioneel)
    cluster = models.ForeignKey(Cluster, on_delete=models.PROTECT,
                                null=True, blank=True)      # cluster is optioneel

    # het week nummer van deze ronde
    # moet liggen in een toegestane reeks (afhankelijk van 18m/25m)
    week_nr = models.PositiveSmallIntegerField()

    # een eigen beschrijving van deze ronde
    # om gewone rondes en inhaalrondes uit elkaar te houden
    beschrijving = models.CharField(max_length=40)

    # wedstrijdenplan voor deze competitie ronde
    matches = models.ManyToManyField(CompetitieMatch, blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.cluster:
            msg = str(self.cluster)
        else:
            msg = str(self.regiocomp.regio)

        msg += " week %s" % self.week_nr

        msg += " (%s)" % self.beschrijving
        return msg

    class Meta:
        verbose_name = 'Ronde'


# end of file
