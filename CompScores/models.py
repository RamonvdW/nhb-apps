# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.models import CompetitieMatch


class ExterneScoresImportLogboek(models.Model):

    """ Logboek over de import van externe scores
        In dit logboek slaat de achtergrondtaak de problemen op.
        Bij de invoer van de scores voor een wedstrijd tonen we deze log.
    """

    # bij welke match hoort deze log
    match = models.ForeignKey(CompetitieMatch, on_delete=models.CASCADE)

    logboek = models.TextField(blank=True)

    def __str__(self):
        return "[%s] (length: %s)" % (self.match.id, len(self.logboek))

    class Meta:
        verbose_name = "Externe scores import logboek"
        verbose_name_plural = "Externe scores import logboeken"

# end of file
