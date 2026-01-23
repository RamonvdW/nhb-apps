# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from GoogleDrive.models import Bestand
import datetime


class SheetStatus(models.Model):
    """ Deze tabel houdt bij:
        - stand van zaken voor elk Google Sheets wedstrijdformulier

        Wordt bijgewerkt door operations/monitor_bestanden
    """

    bestand = models.ForeignKey(Bestand, on_delete=models.CASCADE)

    # wanneer is het bestand voor het laatst gewijzigd?
    gewijzigd_op = models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                  tzinfo=datetime.timezone.utc))

    # door wie is de wijziging gedaan?
    gewijzigd_door = models.CharField(max_length=100, default='')

    # wanneer hebben we voor het laatste in het bestand gekeken?
    # als gewijzigd_op > bekeken_op dan moeten we opnieuw kijken
    bekeken_op = models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                tzinfo=datetime.timezone.utc))

    # vastgestelde fase van de wedstrijd
    # - nog niet begonnen
    # - klaar
    # indiv:
    # - voorronde 1 (individueel)
    # - voorronde 2 (individueel)
    # - laatste 16 / 8 / 4
    # - bronzen finale
    # - gouden finale
    # teams:
    # - ronde 1..7
    wedstrijd_fase = models.CharField(max_length=100, default='')

    # bevat dit bestand al scores (dan wordt de deelnemerslijst niet meer bijgewerkt)
    bevat_scores = models.BooleanField(default=False)

    # is de uitslag al compleet?
    uitslag_is_compleet = models.BooleanField(default=False)

    # wanneer is de uitslag geïmporteerd?
    uitslag_ingelezen_op = models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                          tzinfo=datetime.timezone.utc))

    # hoeveel deelnemers bevat dit bestand (individueel of teams)
    aantal_deelnemers = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "[%s] gewijzigd op %s" % (self.pk,
                                         self.gewijzigd_op.strftime('%Y-%m-%d %H:%M:%S'))

    class Meta:
        verbose_name = verbose_name_plural = "Sheet status"


# end of file
