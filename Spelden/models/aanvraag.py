# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import GESLACHT_MV, GESLACHT_MAN
from BasisTypen.models import BoogType, Leeftijdsklasse
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
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT)

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

    ## STAP 2 ##

    # enkele of meerdere afstanden
    # langste: "90, 70, 50, 30" = 12
    afstanden = models.CharField(max_length=15, default='')

    # aantal pijlen
    aantal_pijlen = models.PositiveSmallIntegerField(default=0)

    # aantal doelen
    aantal_doelen = models.PositiveSmallIntegerField(default=0)

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
    door_account = models.ForeignKey(Account, on_delete=models.PROTECT)

    # laatste keer dat we een reminder gemaild hebben aan de aanvrager?
    last_email_reminder = models.DateTimeField(auto_now_add=True)       # zet op 'vandaag" bij aanmaken record

    # voor welke sporter wordt de aanvraag gedaan?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # materiaalklasse
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # wat voor soort aanvraag gaat het om?
    soort_speld = models.CharField(max_length=4,
                                   default=SPELD_CATEGORIE_WA_STER_R,
                                   choices=SPELD_CATEGORIE_CHOICES)

    # op welke datum is de prestatie neergezet?
    datum_wedstrijd = models.DateField()

    # op welke wedstrijd is de prestatie neergezet?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # discipline outdoor/indoor/veld
    discipline = models.CharField(max_length=2,
                                  choices=SPELD_DISCIPLINE_CHOICES,
                                  default=SPELD_DISCIPLINE_NVT)

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
