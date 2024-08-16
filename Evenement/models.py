# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import ORGANISATIE_KHSN
from Evenement.definities import (EVENEMENT_STATUS_CHOICES, EVENEMENT_STATUS_ONTWERP, EVENEMENT_STATUS_TO_STR,
                                  EVENEMENTINSCHRIJVING_STATUS_CHOICES, EVENEMENTINSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENTINSCHRIJVING_STATUS_TO_STR)
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from Vereniging.models import Vereniging
from decimal import Decimal


class Evenement(models.Model):

    """ Een evenement voor op de kalender """

    # titel van het evenement
    titel = models.CharField(max_length=50, default='')

    # status van dit evenement: ontwerp --> goedgekeurd --> geannuleerd
    status = models.CharField(max_length=1, choices=EVENEMENT_STATUS_CHOICES, default=EVENEMENT_STATUS_ONTWERP)

    # wie beheert dit evenement?
    # wordt ook gebruikt voor betalingen
    organiserende_vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT)

    # ter info op de kalender = niet op in te schrijven, dus geen inschrijf deadline tonen
    is_ter_info = models.BooleanField(default=False)

    # wanneer is het evenement
    datum = models.DateField()
    aanvang = models.TimeField(default='10:00')

    # hoeveel dagen van tevoren de online-inschrijving dicht doen?
    inschrijven_tot = models.PositiveSmallIntegerField(default=1)

    # waar wordt het evenement gehouden
    locatie = models.ForeignKey(EvenementLocatie, on_delete=models.PROTECT)

    # contactgegevens van de organisatie
    contact_naam = models.CharField(max_length=50, default='', blank=True)
    contact_email = models.CharField(max_length=150, default='', blank=True)
    contact_website = models.CharField(max_length=100, default='', blank=True)
    contact_telefoon = models.CharField(max_length=50, default='', blank=True)

    # eventuele opmerkingen vanuit de organisatie
    bijzonderheden = models.TextField(max_length=1000, default='',
                                      blank=True)      # mag leeg zijn

    # kosten (voor alle sessies van de hele wedstrijd)
    prijs_euro_normaal = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99
    prijs_euro_onder18 = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    def bepaal_prijs_voor_sporter(self, sporter):
        leeftijd = sporter.bereken_wedstrijdleeftijd(self.datum, ORGANISATIE_KHSN)
        prijs = self.prijs_euro_onder18 if leeftijd < 18 else self.prijs_euro_normaal
        return prijs

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        msg = str(self.datum)
        msg += ' [%s]' % self.organiserende_vereniging.ver_nr
        msg += ' %s %s' % (EVENEMENT_STATUS_TO_STR[self.status], self.titel)
        return msg

    class Meta:
        verbose_name = "Evenement"
        verbose_name_plural = "Evenementen"

    objects = models.Manager()      # for the editor only


class EvenementInschrijving(models.Model):

    """ Een inschrijving op een evenement, inclusief koper en betaal-status """

    # wanneer is deze inschrijving aangemaakt?
    wanneer = models.DateTimeField()

    # status
    status = models.CharField(max_length=2, choices=EVENEMENTINSCHRIJVING_STATUS_CHOICES,
                              default=EVENEMENTINSCHRIJVING_STATUS_RESERVERING_MANDJE)

    # voor welke evenement is dit?
    evenement = models.ForeignKey(Evenement, on_delete=models.PROTECT)

    # voor welk lid is deze inschrijving
    sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT)

    # wie is de koper?
    # (BestelProduct verwijst naar deze inschrijving)
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # log van bestelling, betalingen en eventuele wijzigingen van klasse en sessie
    log = models.TextField(blank=True)

    # TODO: traceer de gestuurde emails

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Inschrijving voor %s: [%s]" % (self.sporter.lid_nr_en_volledige_naam(),
                                               EVENEMENTINSCHRIJVING_STATUS_TO_STR[self.status])

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze inschrijving """

        titel = self.evenement.titel
        if len(titel) > 60:
            titel = titel[:58] + '..'

        return "%s - %s" % (self.sporter.lid_nr, titel)

    class Meta:
        verbose_name = "Evenement inschrijving"
        verbose_name_plural = "Evenement inschrijvingen"

        constraints = [
            # constraint zodat sporter niet meerdere keren kan aanmelden
            models.UniqueConstraint(fields=('evenement', 'sporter'),
                                    name='Geen dubbele evenement inschrijving'),
        ]

    objects = models.Manager()      # for the editor only


# end of file
