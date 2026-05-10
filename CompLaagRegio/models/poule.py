# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from .regiocomp import RegioComp
from .team import RegioTeam


class RegioPoule(models.Model):

    """ Een poule wordt gebruikt om teams direct tegen elkaar uit te laten komen.
        Tot 8 teams kunnen in een poule geplaatst worden; verder aangevuld met dummies.
    """

    # bij welke regiocompetitie hoort deze poule?
    regiocomp = models.ForeignKey(RegioComp, on_delete=models.CASCADE)

    # naam van de poule, bijvoorbeeld "ERE + A"
    beschrijving = models.CharField(max_length=100, default='')

    # welke teams zijn in deze poule geplaatst?
    teams = models.ManyToManyField(RegioTeam,
                                   blank=True)      # mag leeg zijn

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving

    class Meta:
        verbose_name = 'Poule'


# end of file
