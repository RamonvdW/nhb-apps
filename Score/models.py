# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import models
from BasisTypen.models import BoogType
from Account.models import Account
from Schutter.models import SchutterBoog


class Score(models.Model):
    """ Bijhouden van een specifieke score """

    # schutter-boog waar deze score bij hoort
    schutterboog = models.ForeignKey(SchutterBoog, on_delete=models.CASCADE)

    # een aanvangsgemiddelde wordt hier ook opgeslagen met drie decimalen
    # nauwkeurig als AG*1000. Dus 9,123 --> 9123
    # hierdoor kunnen we gebruik maken van de ScoreHist

    # waarde van de score, bijvoorbeeld 360
    waarde = models.PositiveSmallIntegerField()     # max = 32767

    # 18, 25, 70, etc.
    afstand_meter = models.PositiveSmallIntegerField()


class ScoreHist(models.Model):
    """ Bijhouden van de geschiedenis van een score: invoer en wijzigingen """

    score = models.ForeignKey(Score, on_delete=models.CASCADE)

    oude_waarde = models.PositiveSmallIntegerField()
    nieuwe_waarde = models.PositiveSmallIntegerField()

    # datum van wijziging
    datum = models.DateField()

    # wie heeft de wijziging gedaan
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

    # notitie bij de wijziging
    notitie = models.CharField(max_length=100)


# end of file
