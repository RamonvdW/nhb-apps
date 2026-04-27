# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import KalenderWedstrijdklasse
from Bestelling.models import BestellingRegel
from Sporter.models import SporterBoog
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_CHOICES,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR,
                                    KWALIFICATIE_CHECK_CHOICES, KWALIFICATIE_CHECK_NOG_DOEN)
from decimal import Decimal
from .korting import WedstrijdKorting
from .sessie import WedstrijdSessie
from .wedstrijd import Wedstrijd


class WedstrijdInschrijving(models.Model):

    """ Een inschrijving op een wedstrijd sessie, inclusief koper, betaal-status en gebruikte korting """

    # wanneer is deze inschrijving aangemaakt?
    wanneer = models.DateTimeField()

    # het unieke nummer om aan deze reservering/bestelling te refereren
    #reserveringsnummer = models.BigIntegerField()      # TODO: toevoegen ipv het pk gebruiken

    # status
    status = models.CharField(max_length=2, choices=WEDSTRIJD_INSCHRIJVING_STATUS_CHOICES,
                              default=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

    # voor welke wedstrijd is dit?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT)

    # voor welke sessie?
    sessie = models.ForeignKey(WedstrijdSessie, on_delete=models.PROTECT, null=True, blank=True)

    # voor wie is deze inschrijving
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT)

    # in welke klasse komt deze sporterboog uit?
    wedstrijdklasse = models.ForeignKey(KalenderWedstrijdklasse, on_delete=models.PROTECT)

    # koppeling aan het mandje / een bestelling
    bestelling = models.ForeignKey(BestellingRegel, on_delete=models.PROTECT, null=True)

    # wie is de koper?

    # (BestellingProduct verwijst naar deze inschrijving)           # TODO: klopt dit nog?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)    # TODO: Bestelling heeft koper, dus waarom hier ook?

    # welke korting is gebruikt
    korting = models.ForeignKey(WedstrijdKorting, on_delete=models.SET_NULL, blank=True, null=True)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # log van bestelling, betalingen en eventuele wijzigingen van klasse en sessie
    log = models.TextField(blank=True)

    # TODO: traceer de gestuurde emails

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Wedstrijd inschrijving voor %s, voor wedstrijd %s, status %s" % (
                    self.sporterboog.sporter.lid_nr_en_volledige_naam(),
                    self.wedstrijd.titel,
                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[self.status])

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze inschrijving """

        titel = self.wedstrijd.titel
        if len(titel) > 60:
            titel = titel[:58] + '..'

        return "%s - %s - %s" % (self.sporterboog.sporter.lid_nr,
                                 self.sporterboog.boogtype.beschrijving,
                                 titel)

    class Meta:
        verbose_name = "Wedstrijd inschrijving"
        verbose_name_plural = "Wedstrijd inschrijvingen"

        constraints = [
            # constraint op een sessie i.p.v. wedstrijd zodat sporter mee kan doen met meerdere sessies,
            # bijvoorbeeld zaterdag/zondag of ochtend/middag
            models.UniqueConstraint(fields=('sessie', 'sporterboog'),
                                    name='Geen dubbele wedstrijd inschrijving'),
        ]

    objects = models.Manager()      # for the editor only


class Kwalificatiescore(models.Model):

    # voor welke inschrijving is dit?
    inschrijving = models.ForeignKey(WedstrijdInschrijving, on_delete=models.CASCADE)

    # wanneer was de wedstrijd
    datum = models.DateField(default='2000-01-01')

    # naam van de wedstrijd
    naam = models.CharField(max_length=50)

    # locatie van de wedstrijd (plaats + land)
    waar = models.CharField(max_length=50)

    # behaald resultaat
    resultaat = models.PositiveSmallIntegerField(default=0)

    # controle status
    check_status = models.CharField(max_length=1, default=KWALIFICATIE_CHECK_NOG_DOEN,
                                    choices=KWALIFICATIE_CHECK_CHOICES)

    log = models.TextField(default='')

    def __str__(self):
        return "[%s] %s: %s (%s)" % (self.datum, self.resultaat, self.naam, self.waar)

    objects = models.Manager()      # for the editor only


# end of file
