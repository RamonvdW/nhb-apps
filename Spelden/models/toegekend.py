# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from .spelden import Speld
from Sporter.models import Sporter


class SpeldToegekend(models.Model):
    """ Deze tabel houdt de behaalde spelden/veren/schilden van een sporter bij """

    # welke speld heeft de sporter behaald?
    speld = models.ForeignKey(Speld, on_delete=models.PROTECT)

    # welke sporter heeft deze speelsterkte behaald?
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # wanneer is deze speld toegekend?
    datum = models.DateField()

    # Senior / Master / Cadet
    # sommige spelden zijn apart te behalen in verschillende categorieën
    category = models.CharField(max_length=50)      # FUTURE: Obsolete

    def __str__(self):
        return "[%s] %s - %s (%s) " % (self.datum, self.speld.beschrijving,
                                       self.sporter.volledige_naam(), self.category)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Speld toegekend"


# end of file
