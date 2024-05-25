# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import BoogType, Leeftijdsklasse
from Spelden.definities import (SPELD_CATEGORIE_CHOICES, SPELD_CATEGORIE_WA_STER,
                                SOORT_BIJLAGE_CHOICES, SOORT_BIJLAGE_SCOREBRIEFJE,
                                SOORT_BESTAND_CHOICES, SOORT_BESTAND_FOTO,
                                WEDSTRIJD_DISCIPLINE_CHOICES, WEDSTRIJD_DISCIPLINE_OUTDOOR)
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd


class Speld(models.Model):
    """ definitie van een fysieke speld """

    # volgorde voor tonen (lager = toon eerder)
    volgorde = models.PositiveSmallIntegerField()

    # sterspeld, target award, etc.
    categorie = models.CharField(max_length=3,
                                 choices=SPELD_CATEGORIE_CHOICES)

    # beschrijving
    # (Grijs, Wit, 1000, etc.)
    beschrijving = models.CharField(max_length=20)

    # recurve, compound, etc.
    # optioneel: niet gezet = geldt voor alle bogen
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT,
                                  null=True, blank=True)

    def __str__(self):
        return "%s %s %s" % (self.categorie, self.volgorde, self.beschrijving)

    class Meta:
        verbose_name = "Speld"
        verbose_name_plural = "Spelden"


class SpeldLimiet(models.Model):

    # opsplitsing in leeftijdsklasse en geslacht
    # (O14/O18/O21/Senior/50+, M/V)
    leeftijdsklasse = models.ForeignKey(Leeftijdsklasse, on_delete=models.PROTECT)

    # afstand (in meters)
    afstand = models.PositiveSmallIntegerField()

    # aantal doelen
    aantal_doelen = models.PositiveSmallIntegerField()

    # welke speld kan er behaald worden?
    speld = models.ForeignKey(Speld, on_delete=models.PROTECT)

    # benodigde score
    benodigde_score = models.PositiveSmallIntegerField()

    def __str__(self):
        return "%s %s %s" % (self.afstand, self.aantal_doelen, self.benodigde_score)

    class Meta:
        verbose_name = "Speld limiet"
        verbose_name_plural = "Speld limieten"


class SpeldAanvraag(models.Model):
    """ Aanvraag prestatiespeld """

    # een datumstempel om een aanvraag op te kunnen ruimen als deze niet afgemaakt wordt
    aangemaakt_op = models.DateField(auto_now_add=True)

    # door wie wordt de aanvraag gedaan?
    door_account = models.ForeignKey(Account, on_delete=models.PROTECT)

    # laatste keer dat we een reminder gemaild hebben aan de aanvrager?
    last_email_reminder = models.DateTimeField(default='2000-01-01')

    # voor welke sporter wordt de aanvraag gedaan?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # materiaalklasse
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # wat voor soort aanvraag gaat het om?
    soort_speld = models.CharField(max_length=3,
                                   default=SPELD_CATEGORIE_WA_STER,
                                   choices=SPELD_CATEGORIE_CHOICES)

    # op welke datum is de prestatie neergezet?
    datum_wedstrijd = models.DateField()

    # op welke wedstrijd is de prestatie neergezet?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # discipline outdoor/indoor/veld
    discipline = models.CharField(max_length=2,
                                  default=WEDSTRIJD_DISCIPLINE_OUTDOOR,
                                  choices=WEDSTRIJD_DISCIPLINE_CHOICES)

    # categorie (O14/O18/O21/Senior/50+, M/V)
    leeftijdsklasse = models.ForeignKey(Leeftijdsklasse, on_delete=models.PROTECT,
                                        null=True, blank=True)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    def __str__(self):
        return "(%s) [%s] %s" % (self.pk, self.datum_wedstrijd, self.door_account.volledige_naam())

    class Meta:
        verbose_name = "Speld aanvraag"
        verbose_name_plural = "Speld aanvragen"


class SpeldBijlage(models.Model):
    """ Bijlage (foto, uitslag) bij een aanvraag prestatiespeld """

    # bij welke aanvraag hoort deze bijlage?
    aanvraag = models.ForeignKey(SpeldAanvraag, on_delete=models.CASCADE)

    # type bijlage
    soort_bijlage = models.CharField(max_length=1, default=SOORT_BIJLAGE_SCOREBRIEFJE, choices=SOORT_BIJLAGE_CHOICES)

    # bestandstype
    bestandstype = models.CharField(max_length=1, default=SOORT_BESTAND_FOTO, choices=SOORT_BESTAND_CHOICES)

    # bestandsnaam is automatisch

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    class Meta:
        verbose_name = "Speld bijlage"
        verbose_name_plural = "Speld bijlagen"


# end of file
