# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import BoogType
from Spelden.definities import SPELD_CATEGORIE_CHOICES, SPELD_CATEGORIE2STR


class Speld(models.Model):
    """ definitie van een fysieke speld """

    # volgorde voor tonen (lager = toon eerder)
    volgorde = models.PositiveSmallIntegerField()

    # sterspeld, target award, etc.
    categorie = models.CharField(max_length=4,
                                 choices=SPELD_CATEGORIE_CHOICES)

    # beschrijving
    # (Grijs, Wit, 1000, etc.)
    beschrijving = models.CharField(max_length=40)

    # ster spelden hebben aparte ontwerpen voor recurve en compound
    # voor de rest is dit veld niet gezet
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # afkorting om te tonen op de bondspas (langste: AH24-ZWART)
    pas_code = models.CharField(max_length=10, default='', blank=True)

    def __str__(self):
        cat_str = SPELD_CATEGORIE2STR.get(self.categorie, '?? (%s)' % self.categorie)
        msg = "%s: %s, %s" % (self.volgorde, cat_str, self.beschrijving)
        # if self.boog_type:
        #     msg += ' (%s)' % self.boog_type.beschrijving
        return msg

    class Meta:
        verbose_name = "Speld"
        verbose_name_plural = "Spelden"


# end of file
