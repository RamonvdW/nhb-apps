# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.models import Competitie, CompetitieMatch
from Functie.models import Functie
from Geo.models import Rayon


class KampRK(models.Model):

    """ Deze tabel bevat informatie over een deel van de kampioenschappen 4x RK indiv en teams """

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # rayon, voor RK
    rayon = models.ForeignKey(Rayon, on_delete=models.PROTECT,
                              null=True, blank=True)    # optioneel want alleen voor RK

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    # wedstrijden
    matches = models.ManyToManyField(CompetitieMatch, blank=True)

    # heeft deze RK/BK al een vastgestelde deelnemerslijst?
    heeft_deelnemerslijst = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = str(self.competitie) + ' Rayon %s' % self.rayon.rayon_nr
        return msg

    class Meta:
        verbose_name = "KampRK"
        ordering = ['competitie__afstand', 'rayon__rayon_nr']


# end of file
