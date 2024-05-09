# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Prestatiespelden.definities import SPELDSOORT_CHOICES, SPELDSOORT_WA_STER
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd


class SpeldAanvraag(models.Model):
    """ Aanvraag prestatiespeld """

    # een datumstempel om een aanvraag op te kunnen ruimen als deze niet afgemaakt wordt
    aangemaakt_op = models.DateField(auto_now_add=True)

    # door wie wordt de aanvraag gedaan?
    door_account = models.ForeignKey(Account, on_delete=models.PROTECT)

    # voor welke sporter wordt de aanvraag gedaan?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # laatste keer dat we een reminder gemaild hebben aan de aanvrager?
    last_email_reminder = models.DateTimeField(default='2000-01-01')

    # wat voor soort aanvraag gaat het om?
    soort = models.CharField(max_length=2, default=SPELDSOORT_WA_STER, choices=SPELDSOORT_CHOICES)

    # op welke datum is de prestatie neergezet?
    datum_wedstrijd = models.DateField()

    # op welke wedstrijd is de prestatie neergezet?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # voor wedstrijden die niet op de kalender staan kunnen details met de hand ingevoerd worden
    externe_wedstrijd_plaats = models.CharField(max_length=75, default='', blank=True)
    externe_wedstrijd_soort = models.CharField(max_length=10, default='', blank=True)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    def __str__(self):
        return "(%s) [%s] %s" % (self.pk, self.datum_wedstrijd, self.door_account.volledige_naam())

    class Meta:
        verbose_name_plural = verbose_name = "Scheids beschikbaarheid"


class SpeldBijlage(models.Model):
    """ Bijlage (foto, uitslag) bij een aanvraag prestatiespeld """

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

    opmerking = models.CharField(max_length=100, default='', blank=True)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    def __str__(self):
        return "%s  %s: %s (%s)" % (self.scheids.lid_nr, self.datum, BESCHIKBAAR2STR[self.opgaaf], self.wedstrijd.titel)

    class Meta:
        verbose_name_plural = verbose_name = "Scheids beschikbaarheid"


# end of file
