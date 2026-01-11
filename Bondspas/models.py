# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


class BondspasJaar(models.Model):
    """ Deze tabel bevat informatie over de bondspas voor elk jaar """

    # mag deze al getoond worden, of moeten we de pas van vorig jaar nog tonen?
    zichtbaar = models.BooleanField(default=False)

    # voor welk jaar is dit achtergrondplaatje
    jaar = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "Jaar %s; zichtbaar=%s" % (self.jaar, self.zichtbaar)

    class Meta:
        verbose_name = "Bondspas jaar"
        verbose_name_plural = "Bondspas jaren"
        ordering = ['-jaar']

    objects = models.Manager()      # for the editor only


# end of file
