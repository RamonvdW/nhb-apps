# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


# leden zijn junior tot en met het jaar waarin ze 20 worden
MAXIMALE_LEEFTIJD_JEUGD = 20


class BoogType(models.Model):
    """ boog typen: volledige naam en unique afkorting """
    beschrijving = models.CharField(max_length=50)
    afkorting = models.CharField(max_length=5)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.CharField(max_length=1, default='?')

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog type"
        verbose_name_plural = "Boog types"


class LeeftijdsKlasse(models.Model):
    """ definitie van een leeftijdsklasse """
    GESLACHT = [('M', 'Man'), ('V', 'Vrouw')]
    afkorting = models.CharField(max_length=5)
    beschrijving = models.CharField(max_length=80)      # CH Cadetten, mannen
    klasse_kort = models.CharField(max_length=30)       # Cadet, Junior, etc.
    geslacht = models.CharField(max_length=1, choices=GESLACHT)
    min_wedstrijdleeftijd = models.IntegerField(default=0)
    max_wedstrijdleeftijd = models.IntegerField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s %s" % (self.afkorting,
                          self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Leeftijdsklasse"
        verbose_name_plural = "Leeftijdsklassen"


class IndivWedstrijdklasse(models.Model):
    """ definitie van een wedstrijdklasse """
    buiten_gebruik = models.BooleanField(default=False)     # niet meer gebruiken?
    beschrijving = models.CharField(max_length=80)
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)
    volgorde = models.PositiveIntegerField()                # lager nummer = betere schutters
    leeftijdsklassen = models.ManyToManyField(LeeftijdsKlasse)
    niet_voor_rk_bk = models.BooleanField()                 # aspirant klassen
    is_onbekend = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijdklasse"
        verbose_name_plural = "Wedstrijdklassen"


class TeamWedstrijdklasse(models.Model):
    """ definitie van een team wedstrijdklasse """
    buiten_gebruik = models.BooleanField(default=False)     # niet meer gebruiken?
    beschrijving = models.CharField(max_length=80)
    boogtypen = models.ManyToManyField(BoogType)
    volgorde = models.PositiveIntegerField()                # lager nummer = betere schutters

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team Wedstrijdklasse"
        verbose_name_plural = "Team Wedstrijdklassen"

# end of file
