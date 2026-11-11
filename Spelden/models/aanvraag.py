# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import GESLACHT_MV, GESLACHT_MAN
from BasisTypen.models import BoogType, Leeftijdsklasse
from Bestelling.models import BestellingRegel
from Spelden.definities import (SPELD_CATEGORIE_CHOICES, SPELD_CATEGORIE_WA_STER_R,
                                SPELD_DISCIPLINE_CHOICES, SPELD_DISCIPLINE_NVT,
                                SPELD_BOOGTYPE_CHOICES,
                                SOORT_BIJLAGE_CHOICES, SOORT_BIJLAGE_SCOREBRIEFJE,
                                SOORT_BESTAND_CHOICES, SOORT_BESTAND_FOTO)
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd


class SpeldAanvraagPrep(models.Model):

    # een datumstempel om een aanvraag op te kunnen ruimen als deze niet afgemaakt wordt
    aangemaakt_op = models.DateField(auto_now_add=True)

    # door wie wordt de aanvraag gedaan?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # voor arrowhead spelden (discipline veld) zijn de scores verschillend voor mannen en vrouwen
    wedstrijd_geslacht = models.CharField(max_length=1, choices=GESLACHT_MV, default=GESLACHT_MAN)

    # stap1 = discipline, boogtype, score
    heeft_data_stap1 = models.BooleanField(default=False)
    heeft_data_stap2 = models.BooleanField(default=False)
    heeft_data_stap3 = models.BooleanField(default=False)

    ## STAP 1 ##

    # discipline outdoor/indoor/veld
    # welke discipline is dit? (indoor/outdoor/veld, etc.)
    discipline = models.CharField(max_length=2, choices=SPELD_DISCIPLINE_CHOICES, default=SPELD_DISCIPLINE_NVT)

    # boogtype
    boog = models.CharField(max_length=2, choices=SPELD_BOOGTYPE_CHOICES, default=SPELD_BOOGTYPE_CHOICES[0][0])

    # behaalde score
    score = models.PositiveSmallIntegerField(default=0)

    # op welke datum is de prestatie neergezet?
    datum_wedstrijd = models.DateField(default="2000-01-01")

    ## STAP 2 ##

    # enkele of meerdere afstanden
    # langste: "90, 70, 50, 30" = 12
    afstanden = models.CharField(max_length=15, default='')

    # aantal pijlen
    aantal_pijlen = models.PositiveSmallIntegerField(default=0)

    # aantal doelen
    aantal_doelen = models.PositiveSmallIntegerField(default=0)

    ## STAP 3 ##

    # op welke wedstrijd is de prestatie neergezet?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.SET_NULL, null=True, blank=True)

    informatie_wedstrijd = models.CharField(max_length=128, default='', blank=True)

    def __str__(self):
        msg = "%s: " % self.voor_sporter.lid_nr_en_volledige_naam()
        if self.heeft_data_stap3:
            msg += ' stap 3'
        elif self.heeft_data_stap2:
            msg += ' stap 2'
        elif self.heeft_data_stap1:
            msg += ' stap 1'
        return msg

    class Meta:
        verbose_name = verbose_name_plural = "Speld aanvraag prep"


class SpeldAanvraag(models.Model):
    """ Aanvraag prestatiespeld """

    # een datumstempel om een aanvraag op te kunnen ruimen als deze niet afgemaakt wordt
    aangemaakt_op = models.DateField(auto_now_add=True)

    # door wie wordt de aanvraag gedaan?
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    # voor welke sporter wordt de aanvraag gedaan?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # voor arrowhead spelden (discipline veld) zijn de scores verschillend voor mannen en vrouwen
    wedstrijd_geslacht = models.CharField(max_length=1, choices=GESLACHT_MV, default=GESLACHT_MAN)

    # om welke speld gaat dit?
    speld = models.CharField(max_length=4,
                             default=SPELD_CATEGORIE_WA_STER_R,
                             choices=SPELD_CATEGORIE_CHOICES)

    # discipline outdoor/indoor/veld
    discipline = models.CharField(max_length=2,
                                  choices=SPELD_DISCIPLINE_CHOICES,
                                  default=SPELD_DISCIPLINE_NVT)

    # boogtype
    boog = models.CharField(max_length=2, choices=SPELD_BOOGTYPE_CHOICES, default=SPELD_BOOGTYPE_CHOICES[0][0])

    # behaalde score
    score = models.PositiveSmallIntegerField(default=0)

    # op welke datum is de prestatie neergezet?
    datum_wedstrijd = models.DateField()

    # op welke wedstrijd is de prestatie neergezet?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.SET_NULL, null=True, blank=True)

    informatie_wedstrijd = models.CharField(max_length=128, default='', blank=True)

    # koppeling aan het mandje / een bestelling
    bestelling_regel = models.ForeignKey(BestellingRegel, on_delete=models.CASCADE, null=True, blank=True)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    def __str__(self):
        return "(%s) [%s] %s" % (self.pk, self.datum_wedstrijd, self.door_account.volledige_naam())

    class Meta:
        verbose_name = "Speld aanvraag"
        verbose_name_plural = "Speld aanvragen"


# end of file
