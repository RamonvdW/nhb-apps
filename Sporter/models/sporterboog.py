# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import BoogType
from .sporter import Sporter


class SporterBoog(models.Model):
    """ Sporter met een specifiek type boog en zijn voorkeuren
        er is een record voor elk type boog
    """
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE, null=True)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)

    # voorkeuren van de sporter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    # aanvangsgemiddelde is opgeslagen in een Aanvangsgemiddelde en AanvangsgemiddeldeHist record

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SporterBoog"
        verbose_name_plural = "SporterBoog"

        ordering = ['sporter__lid_nr', 'boogtype__volgorde']

        unique_together = ('sporter', 'boogtype')

        indexes = [
            # ondersteuning voor filteren op voor_wedstrijd=True
            models.Index(fields=['voor_wedstrijd'])
        ]

    def __str__(self):
        # voorkom exceptie als sporter op None staat
        if self.sporter:
            return "%s - %s" % (self.sporter.lid_nr, self.boogtype.beschrijving)
        else:
            # komt voor als we een fake ScoreHist record aanmaken om de background task te kietelen
            return "sporter? - %s" % self.boogtype.beschrijving

    objects = models.Manager()      # for the editor only


# end of file
