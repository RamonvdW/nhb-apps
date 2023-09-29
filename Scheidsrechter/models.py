# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Scheidsrechter.definities import BESCHIKBAAR_CHOICES, BESCHIKBAAR2STR, BESCHIKBAAR_LEEG
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd


class ScheidsBeschikbaarheid(models.Model):
    """ Bijhouden van de beschikbaarheid van een scheidsrechter voor een specifieke datum """

    # over welke scheidsrechter gaat dit?
    scheids = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # voor welke wedstrijd is de behoefte?
    # (dit is nodig om meerdere wedstrijden per dag te ondersteunen)
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE)

    # over welke datum gaat dit?
    # deze zetten we hier vast voor het geval de wedstrijd verplaatst wordt
    datum = models.DateField()

    # de laatste keuze voor de beschikbaarheid
    opgaaf = models.CharField(max_length=1, choices=BESCHIKBAAR_CHOICES, default=BESCHIKBAAR_LEEG)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='')

    def __str__(self):
        return "%s  %s: %s (%s)" % (self.scheids.lid_nr, self.datum, BESCHIKBAAR2STR[self.opgaaf], self.wedstrijd.titel)

    class Meta:
        verbose_name_plural = verbose_name = "Scheids beschikbaarheid"

    objects = models.Manager()      # for the editor only


class WedstrijdDagScheids(models.Model):
    """ Bijhouden van de scheidsrechter behoefte voor een specifieke wedstrijd
        en de gekozen scheidsrechters.
    """

    # voor welke wedstrijd is de behoefte?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE)

    # voor elke dag van de wedstrijd een specifieke behoefte
    # eerste dag is 0
    dag_offset = models.SmallIntegerField(default=0)

    # om in consistente volgorde te kunnen tonen
    volgorde = models.SmallIntegerField(default=0)

    # wat voor soort behoefte gaat dit om?
    # Hoofdscheidsrechter / Assistent SR, etc.
    titel = models.CharField(max_length=20, default='')

    is_hoofd_sr = models.BooleanField(default=False)

    # welke scheidsrechter is gekozen voor deze positie?
    gekozen = models.ForeignKey(Sporter, on_delete=models.SET_NULL,
                                null=True, blank=True)              # mag leeg zijn

    def __str__(self):
        msg = "[%s +%s] %s = " % (self.wedstrijd.datum_begin, self.dag_offset, self.titel)
        if self.gekozen:
            msg += self.gekozen.lid_nr_en_volledige_naam()
        else:
            msg += '?'
        return msg

    class Meta:
        verbose_name_plural = verbose_name = "Wedstrijddag scheids"

    objects = models.Manager()      # for the editor only


# end of file
