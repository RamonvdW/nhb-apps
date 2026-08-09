# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import GESLACHT_MV, GESLACHT_MAN
from BasisTypen.models import BoogType, Leeftijdsklasse
from Spelden.definities import (SPELD_CATEGORIE_CHOICES, SPELD_CATEGORIE2STR, SPELD_CATEGORIE_WA_STER,
                                SPELD_DISCIPLINE_CHOICES, SPELD_DISCIPLINE_NVT, SPELD_DISCIPLINE2STR,
                                SPELD_BOOGTYPE_CHOICES,
                                SOORT_BIJLAGE_CHOICES, SOORT_BIJLAGE_SCOREBRIEFJE,
                                SOORT_BESTAND_CHOICES, SOORT_BESTAND_FOTO)
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd
from decimal import Decimal


class Speld(models.Model):
    """ definitie van een fysieke speld """

    # volgorde voor tonen (lager = toon eerder)
    volgorde = models.PositiveSmallIntegerField()

    # sterspeld, target award, etc.
    categorie = models.CharField(max_length=3,
                                 choices=SPELD_CATEGORIE_CHOICES)

    # beschrijving
    # (Grijs, Wit, 1000, etc.)
    beschrijving = models.CharField(max_length=30)

    # ster spelden hebben aparte ontwerpen voor recurve en compound
    # voor de rest is dit veld niet gezet
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # de prijs voor dit product
    # (alleen van toepassing voor vervangen verloren speld)
    prijs_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))        # max 9999,99

    def __str__(self):
        cat_str = SPELD_CATEGORIE2STR.get(self.categorie, '?? (%s)' % self.categorie)
        msg = "%s: %s, %s" % (self.volgorde, cat_str, self.beschrijving)
        # if self.boog_type:
        #     msg += ' (%s)' % self.boog_type.beschrijving
        return msg

    class Meta:
        verbose_name = "Speld"
        verbose_name_plural = "Spelden"


class SpeldVoorwaarden(models.Model):
    """ Voorwaarden om een fysieke speld te kunnen behalen:
        - wedstrijd discpline: outdoor / indoor / veld
        - wedstrijd soort: "70m ronde", etc.
        - boog type: recurve / compound / barebow
        - de afstand(en) waarop geschoten is, bijvoorbeeld "70m" of "50m en 30m" (voor short metric)
        - aantal pijlen dat geschoten is: 50, 60, 72, 90
        - aantal doelen dat geschoten is: 24
        - leeftijdsklasse: onder-21, 21+/senior, 50+/master maar ook man/vrouw
        - benodigde score
    """

    # welke speld kan er behaald worden?
    speld = models.ForeignKey(Speld, on_delete=models.PROTECT)

    # type wedstrijd: outdoor, indoor, veld, n.v.t.
    discipline = models.CharField(max_length=2, choices=SPELD_DISCIPLINE_CHOICES, default=SPELD_DISCIPLINE_NVT)

    # afstanden (enkel of meerdere)
    afstanden = models.CharField(max_length=20, default='', blank=True)

    # (optioneel) beschrijving van het soort wedstrijd waarop de speld te behalen is
    wedstrijd_soort = models.CharField(max_length=20)

    # (optioneel) recurve, compound, etc.
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # (optioneel) specialisatie in leeftijdsklasse en geslacht
    # (O14/O18/O21/Senior/50+, M/V)
    leeftijdsklasse = models.ForeignKey(Leeftijdsklasse, on_delete=models.PROTECT,
                                        null=True, blank=True)

    # benodigde score
    benodigde_score = models.PositiveSmallIntegerField()

    # (optioneel) aantal doelen - wordt alleen gebruikt bij Veld
    aantal_doelen = models.PositiveSmallIntegerField(default=0)

    # (optioneel) aantal pijlen voor dit type wedstrijd - wordt alleen gebruikt bij Outdoor en Indoor
    # (veld heeft aantal doelen * 3 pijlen)
    aantal_pijlen = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        msg = SPELD_DISCIPLINE2STR.get(self.discipline, '?')
        msg += ", %s" % self.wedstrijd_soort
        if self.aantal_doelen:
            msg += ', %s doelen' % self.aantal_doelen
        else:
            msg += ', %sp, %sm' % (self.aantal_pijlen, self.afstanden.replace(', ', '-'))
        if self.boog_type:
            msg += ', %s' % self.boog_type.afkorting
        if self.leeftijdsklasse:
            msg += ', %s' % self.leeftijdsklasse.afkorting
        msg += ', score: %s' % self.benodigde_score
        return msg

    class Meta:
        verbose_name_plural = verbose_name = "Speld voorwaarden"


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
