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

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog type"
        verbose_name_plural = "Boog types"


class TeamType(models.Model):
    """ toegestane team types, zoals Compound """
    beschrijving = models.CharField(max_length=80)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s" % self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team type"
        verbose_name_plural = "Team types"


class WedstrijdKlasse(models.Model):
    """ definitie van een wedstrijdklasse """
    buiten_gebruik = models.BooleanField(default=False)     # niet meer gebruiken?
    beschrijving = models.CharField(max_length=80)
    niet_voor_rk_bk = models.BooleanField()                 # aspirant klassen
    is_voor_teams = models.BooleanField()                   # team klasse?

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        if self.is_voor_teams:
            descr = 'Team'
        else:
            descr = 'Indiv'
        return "%s - %s" % (descr, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijdklasse"
        verbose_name_plural = "Wedstrijdklassen"


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


class TeamTypeBoog(models.Model):
    """ koppelt een team type aan een boog type
        creert toegestane combinaties
        in andere woorden: deze tabel vult een team type met een of meerdere bogen
    """
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)
    teamtype = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s -- %s" % (self.teamtype.beschrijving,
                             self.boogtype.afkorting)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog voor een team type"
        verbose_name_plural = "Bogen voor een team type"


class WedstrijdKlasseBoog(models.Model):
    """ koppelt een wedstrijdklasse aan een boog type
        creert toegestane combinaties
    """
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)
    wedstrijdklasse = models.ForeignKey(WedstrijdKlasse, on_delete=models.PROTECT)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s -- %s" % (self.wedstrijdklasse.beschrijving,
                             self.boogtype.afkorting)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog voor een wedstrijdklasse"
        verbose_name_plural = "Bogen voor elke wedstrijdklasse"


class WedstrijdKlasseLeeftijd(models.Model):
    """ koppelt een wedstrijdklasse aan een leeftijdsklasse
        creert toegestane combinaties
    """
    wedstrijdklasse = models.ForeignKey(WedstrijdKlasse, on_delete=models.PROTECT)
    leeftijdsklasse = models.ForeignKey(LeeftijdsKlasse, on_delete=models.PROTECT)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s -- %s" % (self.wedstrijdklasse.beschrijving,
                             self.leeftijdsklasse.afkorting)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Leeftijdsklasse voor een wedstrijdklasse"
        verbose_name_plural = "Leeftijdsklassen voor elk wedstrijdklasse"


# end of file
