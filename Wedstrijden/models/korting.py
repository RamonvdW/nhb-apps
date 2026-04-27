# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Sporter.models import Sporter
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_KORTING_SOORT_CHOICES, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_COMBI,
                                    WEDSTRIJD_KORTING_SOORT_TO_STR)
from .wedstrijd import Wedstrijd
from typing import Tuple


class WedstrijdKorting(models.Model):

    """ Een korting voor een specifieke sporter, leden van een vereniging of voor een combinatie van wedstrijden """

    # de korting kan voor een specifieke sporter zijn (voorbeeld: winnaar van vorige jaar)
    # de korting kan voor alle leden van een vereniging zijn (voorbeeld: de organiserende vereniging)
    # de korting kan een combinatie-korting geven (meerdere wedstrijden)
    soort = models.CharField(max_length=1,
                             choices=WEDSTRIJD_KORTING_SOORT_CHOICES,
                             default=WEDSTRIJD_KORTING_VERENIGING)

    # tot wanneer geldig?
    geldig_tot_en_met = models.DateField()

    # welke vereniging heeft deze korting uitgegeven? (en mag deze dus wijzigen)
    uitgegeven_door = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='wedstrijd_korting_uitgever')

    # hoeveel korting: 0..100 (procent)
    percentage = models.PositiveSmallIntegerField(default=100)

    # voor welke wedstrijden is deze geldig?
    # bij combi-korting: lijst van alle wedstrijden waar op ingeschreven moeten zijn
    voor_wedstrijden = models.ManyToManyField(Wedstrijd)

    # voor welke individuele sporter is deze korting?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return "%s: [%s] %s %d%%" % (self.pk,
                                     self.uitgegeven_door.pk,
                                     WEDSTRIJD_KORTING_SOORT_TO_STR[self.soort],
                                     self.percentage)

    class Meta:
        verbose_name = "Wedstrijd korting"
        verbose_name_plural = "Wedstrijd kortingen"

    objects = models.Manager()      # for the editor only


def beschrijf_korting(korting: WedstrijdKorting) -> Tuple[str, list]:
    kort_str = ''
    redenen = list()

    if korting.soort == WEDSTRIJD_KORTING_SPORTER:
        kort_str = "Persoonlijke korting: %d%%" % korting.percentage

    elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
        kort_str = "Verenigingskorting: %d%%" % korting.percentage

    elif korting.soort == WEDSTRIJD_KORTING_COMBI:  # pragma: no branch
        kort_str = "Combinatiekorting: %d%%" % korting.percentage
        redenen = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.order_by('datum_begin')]

    return kort_str, redenen

# end of file
