# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


class MandjeTransacties(models.Model):

    """ Compleet logboek van aankopen en terug betalingen """

    # wanneer uitgevoerd?
    wanneer = models.DateTimeField()

    # bedrag
    euros = models.DecimalField(max_digits=7, decimal_places=2)     # max=99999,99

    # wie heeft het bedrag gestuurd
    zender = models.CharField(max_length=200)

    # wie is de ontvanger van het bedrag?
    ontvanger = models.CharField(max_length=200)


# end of file
