# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import KalenderWedstrijdklasse
from Bestelling.models import BestellingRegel
from Sporter.models import SporterBoog
from decimal import Decimal
from .korting import WedstrijdKorting
from .wedstrijd import Wedstrijd


class WedstrijdAfgemeld(models.Model):

    """ Alle details van een afmelding van een eerdere inschrijving op een wedstrijd sessie """

    # wanneer was de afmelding
    wanneer_afgemeld = models.DateTimeField()

    # wanneer was de originele inschrijving?
    wanneer_inschrijving = models.DateTimeField()

    # wat was het originele reserveringsnummer?
    reserveringsnummer = models.BigIntegerField()

    # voor welke wedstrijd was dit?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT)

    # voor wie is deze inschrijving?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT)

    # voor welke sessie was de sporter ingeschreven?
    sessie = models.CharField(max_length=100, default='')

    # in welke klasse wilde deze sporterboog uitkomen?
    wedstrijdklasse = models.ForeignKey(KalenderWedstrijdklasse, on_delete=models.PROTECT)

    # koppeling aan de bestelling
    bestelling = models.ForeignKey(BestellingRegel, on_delete=models.PROTECT, null=True)

    # wie is de koper?
    # (BestellingProduct verwijst naar deze inschrijving)           # TODO: klopt dit nog?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)    # TODO: Bestelling heeft koper, dus waarom hier ook?

    # welke korting was gebruikt?
    korting = models.ForeignKey(WedstrijdKorting, on_delete=models.SET_NULL, blank=True, null=True)

    # bedragen ontvangen en terugbetaald
    bedrag_ontvangen = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    bedrag_retour = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # log van bestelling, betalingen en eventuele wijzigingen van klasse en sessie
    log = models.TextField(blank=True)

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Afgemelding voor %s, voor wedstrijd [%s] %s" % (
                    self.sporterboog.sporter.lid_nr_en_volledige_naam(),
                    self.wedstrijd.datum_begin,
                    self.wedstrijd.titel)

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze inschrijving """

        titel = self.wedstrijd.titel
        if len(titel) > 60:
            titel = titel[:58] + '..'

        return "%s - %s - %s" % (self.sporterboog.sporter.lid_nr,
                                 self.sporterboog.boogtype.beschrijving,
                                 titel)

    class Meta:
        verbose_name = "Wedstrijd afmelding"
        verbose_name_plural = "Wedstrijd afmeldingen"

    objects = models.Manager()      # for the editor only


# end of file
