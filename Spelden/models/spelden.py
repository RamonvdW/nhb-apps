# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import BoogType, Leeftijdsklasse
from Spelden.definities import (SPELD_CATEGORIE_CHOICES, SPELD_CATEGORIE2STR,
                                SPELD_DISCIPLINE_CHOICES, SPELD_DISCIPLINE_NVT, SPELD_DISCIPLINE2STR)
from decimal import Decimal


class Speld(models.Model):
    """ definitie van een fysieke speld """

    # volgorde voor tonen (lager = toon eerder)
    volgorde = models.PositiveSmallIntegerField()

    # sterspeld, target award, etc.
    categorie = models.CharField(max_length=4,
                                 choices=SPELD_CATEGORIE_CHOICES)

    # beschrijving
    # (Grijs, Wit, 1000, etc.)
    beschrijving = models.CharField(max_length=30)

    # ster spelden hebben aparte ontwerpen voor recurve en compound
    # voor de rest is dit veld niet gezet
    boog_type = models.ForeignKey(BoogType, on_delete=models.PROTECT,
                                  null=True, blank=True)

    # afkorting om te tonen op de bondspas
    pas_code = models.CharField(max_length=10, default='', blank=True)

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


# end of file
