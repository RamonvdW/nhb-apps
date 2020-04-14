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

    def __str__(self):
        return "%s %sm - %s" % (self.waarde, self.afstand_meter, self.schutterboog)


class ScoreHist(models.Model):
    """ Bijhouden van de geschiedenis van een score: invoer en wijzigingen """

    score = models.ForeignKey(Score, on_delete=models.CASCADE)

    oude_waarde = models.PositiveSmallIntegerField()
    nieuwe_waarde = models.PositiveSmallIntegerField()

    # datum van wijziging
    datum = models.DateField()

    # wie heeft de wijziging gedaan (null = systeem)
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

    # notitie bij de wijziging
    notitie = models.CharField(max_length=100)

    def __str__(self):
        return "[%s] (%s) %s --> %s: %s" % (self.datum, self.door_account, self.oude_waarde, self.nieuwe_waarde, self.notitie)


def aanvangsgemiddelde_opslaan(schutterboog, afstand, gemiddelde, datum, door_account, notitie):
    """ slaan het aanvangsgemiddelde op voor schutterboog

        Return value:
            True  = opslagen
            False = niet opgeslagen / dupe
    """
    waarde = int(gemiddelde * 1000)

    try:
        score = Score.objects.get(schutterboog=schutterboog, afstand_meter=afstand)
    except Score.DoesNotExist:
        score = Score(schutterboog=schutterboog, waarde=waarde, afstand_meter=afstand)
        score.save()

        hist = ScoreHist(score=score,
                         oude_waarde=0,
                         nieuwe_waarde=waarde,
                         datum=datum,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()
        return True

    if score.waarde != waarde:
        # nieuwe waarde
        hist = ScoreHist(score=score,
                         oude_waarde=score.waarde,
                         nieuwe_waarde=waarde,
                         datum=datum,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()

        score.waarde = waarde
        score.save()
        return True

    hists = ScoreHist.objects.filter(score=score).order_by('-datum')
    if len(hists):
        hist = hists[0]
        if hist.notitie == notitie:
            return False
        print("(no change) score: %s" % score)
        print("            hist: %s" % hist)
    else:
        # geen history, wel een score
        # zou niet voor moeten komen
        pass

    return False

# end of file
