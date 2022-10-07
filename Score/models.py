# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.query_utils import Q
from django.utils.formats import localize
from Account.models import Account
from BasisTypen.models import BoogType
from Sporter.models import SporterBoog


# als een sporter per ongeluk opgenomen is in de uitslag
# dan kan de score aangepast wordt tot SCORE_WAARDE_VERWIJDERD
# om aan te geven dat de sporter eigenlijk toch niet mee deed.
# via scorehist zijn de wijzigingen dan nog in te zien
SCORE_WAARDE_VERWIJDERD = 32767

# gebruik 'geen score' om bij te houden dat gekozen is deze sporterboog te markeren als 'niet geschoten'
# zonder een echt score record aan te maken. Elke sporterboog heeft genoeg aan 1 'geen score' record.
SCORE_TYPE_SCORE = 'S'
# SCORE_TYPE_INDIV_AG = 'I'       # voor de bondscompetities
# SCORE_TYPE_TEAM_AG = 'T'        # voor de bondscompetities
SCORE_TYPE_GEEN = 'G'           # niet geschoten

SCORE_CHOICES = (
    (SCORE_TYPE_SCORE, 'Score'),
    (SCORE_TYPE_GEEN, 'Geen score')
)

AG_DOEL_INDIV = 'i'
AG_DOEL_TEAM = 't'

AG_DOEL_CHOICES = (
    (AG_DOEL_INDIV, 'Individueel'),
    (AG_DOEL_TEAM,  'Teamcompetitie')
)


class Aanvangsgemiddelde(models.Model):
    """ Bijhouden van een specifiek aanvangsgemiddelde """

    # bij wie hoort dit aanvangsgemiddelde
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT)

    # kopie toevoegen van het boogtype van de sporterboog, om eenvoudiger op te kunnen filteren
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # AG voor individueel of team gebruik?
    doel = models.CharField(max_length=1, choices=AG_DOEL_CHOICES, default=AG_DOEL_INDIV)

    # waarde van het aanvangsgemiddelde, bijvoorbeeld 9.123
    waarde = models.DecimalField(max_digits=6, decimal_places=3)     # max = 10,000

    # afstand voor dit aanvangsgemiddelde (18, 25, 70, etc.)
    afstand_meter = models.PositiveSmallIntegerField()

    def __str__(self):
        msg = "[%s] %sm: %s" % (self.sporterboog, self.afstand_meter, self.waarde)

        if self.doel == AG_DOEL_INDIV:
            msg += ' (indiv)'
        else:
            msg += ' (team)'

        return msg

    objects = models.Manager()      # for the editor only


class AanvangsgemiddeldeHist(models.Model):
    """ Bijhouden van de geschiedenis van een aanvangsgemiddelde: vaststellen of invoeer + wijzigingen """

    # datum/tijdstip
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # waar gaat dit over?
    ag = models.ForeignKey(Aanvangsgemiddelde, on_delete=models.CASCADE, null=True, related_name='ag_hist')

    # oude en nieuwe waarde
    oude_waarde = models.DecimalField(max_digits=6, decimal_places=3)     # max = 10,000
    nieuwe_waarde = models.DecimalField(max_digits=6, decimal_places=3)     # max = 10,000

    # wie heeft de wijziging gedaan (null = systeem)
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

    # notitie bij de wijziging
    notitie = models.CharField(max_length=100)

    def __str__(self):
        if self.door_account:
            account_str = str(self.door_account)
        else:
            account_str = 'systeem'

        return "[%s] %s --> %s: %s / door %s" % (localize(self.when), self.oude_waarde, self.nieuwe_waarde, self.notitie, account_str)

    class Meta:
        indexes = [
            # help sorteren op datum
            models.Index(fields=['when'])
        ]

    objects = models.Manager()      # for the editor only


class Score(models.Model):
    """ Bijhouden van een specifieke score """

    # soort: score, indiv ag, team ag
    type = models.CharField(max_length=1, choices=SCORE_CHOICES, default=SCORE_TYPE_SCORE)

    # bij wie hoort deze score
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # TODO: kopie toevoegen van het boogtype van de sporterboog, om eenvoudiger op te kunnen filteren

    # waarde van de score, bijvoorbeeld 360
    # bij indiv/team ag is dit de AG * 1000, dus 9.123 --> 9123
    waarde = models.PositiveSmallIntegerField()     # max = 32767

    # 18, 25, 70, etc.
    afstand_meter = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['sporterboog', 'type'],
                condition=Q(type=SCORE_TYPE_GEEN),
                name='max 1 geen score per sporterboog')
        ]

        indexes = [
            # help filteren op afstand
            models.Index(fields=['afstand_meter']),

            # help filteren op type
            models.Index(fields=['type'])
        ]

    def __str__(self):
        if self.sporterboog:
            msg = "[%s]" % self.sporterboog
        else:
            msg = "[]"

        msg += " %sm" % self.afstand_meter

        if self.type == SCORE_TYPE_GEEN:
            msg += ' (geen score)'
        else:
            msg += ': %s' % self.waarde
        return msg

    objects = models.Manager()      # for the editor only


class ScoreHist(models.Model):
    """ Bijhouden van de geschiedenis van een score: invoer en wijzigingen """

    score = models.ForeignKey(Score, on_delete=models.CASCADE, null=True)

    oude_waarde = models.PositiveSmallIntegerField()
    nieuwe_waarde = models.PositiveSmallIntegerField()

    # datum/tijdstip
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wie heeft de wijziging gedaan (null = systeem)
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

    # notitie bij de wijziging
    notitie = models.CharField(max_length=100)

    def __str__(self):
        return "[%s] (%s) %s --> %s: %s" % (localize(self.when), self.door_account, self.oude_waarde, self.nieuwe_waarde, self.notitie)

    class Meta:
        indexes = [
            # help sorteren op datum
            models.Index(fields=['when'])
        ]

    objects = models.Manager()      # for the editor only


class Uitslag(models.Model):

    # de maximale score die gehaald (en ingevoerd) mag worden
    # dit afhankelijk van het type wedstrijd
    max_score = models.PositiveSmallIntegerField()      # max = 32767

    # 18, 25, 70, etc.
    afstand = models.PositiveSmallIntegerField()

    # scores bevat SporterBoog en komt met ScoreHist
    scores = models.ManyToManyField(Score, blank=True)  # mag leeg zijn / gemaakt worden

    # False = uitslag mag door WL ingevoerd worden
    # True  = uitslag is gecontroleerd en mag niet meer aangepast worden
    is_bevroren = models.BooleanField(default=False)

    def __str__(self):
        msg = "(%s) afstand %s, max score %s" % (self.pk, self.afstand, self.max_score)
        if self.is_bevroren:
            msg += " (bevroren)"
        return msg

    # hier houden we geen klassen bij - het is geen inschrijflijst
    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Uitslag"
        verbose_name_plural = "Uitslagen"


# end of file
