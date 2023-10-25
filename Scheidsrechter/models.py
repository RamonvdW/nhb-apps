# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.db.models.constraints import UniqueConstraint
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

        constraints = [
            UniqueConstraint(
                fields=['scheids', 'wedstrijd', 'datum'],
                name='Een per scheidsrechter en wedstrijd dag')
        ]

    objects = models.Manager()      # for the editor only


class WedstrijdDagScheidsrechters(models.Model):
    """ Bijhouden van de scheidsrechter behoefte voor een specifieke wedstrijd
        en de gekozen scheidsrechters.
    """

    # voor welke wedstrijd is de behoefte?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE)

    # voor elke dag van de wedstrijd een specifieke behoefte
    # eerste dag is 0
    dag_offset = models.SmallIntegerField(default=0)

    # welke hoofdscheidsrechter is gekozen?
    gekozen_hoofd_sr = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_hoofd_sr',
                                         null=True, blank=True)              # mag leeg zijn

    # welke scheidsrechters zijn gekozen?
    gekozen_sr1 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr1', null=True, blank=True)
    gekozen_sr2 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr2', null=True, blank=True)
    gekozen_sr3 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr3', null=True, blank=True)
    gekozen_sr4 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr4', null=True, blank=True)
    gekozen_sr5 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr5', null=True, blank=True)
    gekozen_sr6 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr6', null=True, blank=True)
    gekozen_sr7 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr7', null=True, blank=True)
    gekozen_sr8 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr8', null=True, blank=True)
    gekozen_sr9 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr9', null=True, blank=True)

    def __str__(self):
        return "[%s +%s]" % (self.wedstrijd.datum_begin, self.dag_offset)

    class Meta:
        verbose_name_plural = verbose_name = "Wedstrijddag scheidsrechters"

    objects = models.Manager()      # for the editor only


# end of file
