# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Schutter.models import SchutterBoog


# als een schutter per ongeluk opgenomen is in de uitslag
# dan kan de score aangepast wordt tot SCORE_WAARDE_VERWIJDERD
# om aan te geven dat de schutter eigenlijk toch niet mee deed.
# via scorehist zijn de wijzigingen dan nog in te zien
SCORE_WAARDE_VERWIJDERD = 32767

SCORE_TYPE_SCORE = 'S'
SCORE_TYPE_INDIV_AG = 'I'
SCORE_TYPE_TEAM_AG = 'T'

SCORE_CHOICES = (
    (SCORE_TYPE_SCORE, 'Score'),
    (SCORE_TYPE_INDIV_AG, 'Indiv AG'),
    (SCORE_TYPE_TEAM_AG, 'Team AG')
)


class Score(models.Model):
    """ Bijhouden van een specifieke score """

    # schutter-boog waar deze score bij hoort
    schutterboog = models.ForeignKey(SchutterBoog, on_delete=models.PROTECT)

    # type indicate: score, indiv ag, team ag
    type = models.CharField(max_length=1, choices=SCORE_CHOICES, default=SCORE_TYPE_SCORE)

    # waarde van de score, bijvoorbeeld 360
    # bij indiv/team ag is dit de AG * 1000, dus 9.123 --> 9123
    waarde = models.PositiveSmallIntegerField()     # max = 32767

    # 18, 25, 70, etc.
    afstand_meter = models.PositiveSmallIntegerField()

    def __str__(self):
        msg = "%s - %sm: %s" % (self.schutterboog, self.afstand_meter, self.waarde)
        if self.type == SCORE_TYPE_INDIV_AG:
            msg += ' (indiv AG)'
        elif self.type == SCORE_TYPE_TEAM_AG:
            msg += ' (team AG)'
        return msg

    objects = models.Manager()      # for the editor only


class ScoreHist(models.Model):
    """ Bijhouden van de geschiedenis van een score: invoer en wijzigingen """

    score = models.ForeignKey(Score, on_delete=models.CASCADE)

    oude_waarde = models.PositiveSmallIntegerField()
    nieuwe_waarde = models.PositiveSmallIntegerField()

    # datum/tijdstip
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wie heeft de wijziging gedaan (null = systeem)
    door_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

    # notitie bij de wijziging
    notitie = models.CharField(max_length=100)

    def __str__(self):
        return "[%s] (%s) %s --> %s: %s" % (self.when, self.door_account, self.oude_waarde, self.nieuwe_waarde, self.notitie)

    objects = models.Manager()      # for the editor only


def _score_ag_opslaan(score_type, schutterboog, afstand, gemiddelde, door_account, notitie):
    """ slaan het aanvangsgemiddelde op voor schutterboog

        Return value:
            True  = opslagen
            False = niet opgeslagen / dupe
    """
    waarde = int(gemiddelde * 1000)

    try:
        score = Score.objects.get(schutterboog=schutterboog,
                                  type=score_type,
                                  afstand_meter=afstand)
    except Score.DoesNotExist:
        # eerste aanvangsgemiddelde voor deze afstand
        score = Score(schutterboog=schutterboog,
                      type=score_type,
                      waarde=waarde,
                      afstand_meter=afstand)
        score.save()

        hist = ScoreHist(score=score,
                         oude_waarde=0,
                         nieuwe_waarde=waarde,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()
        return True

    if score.waarde != waarde:
        # nieuwe score voor deze afstand
        hist = ScoreHist(score=score,
                         oude_waarde=score.waarde,
                         nieuwe_waarde=waarde,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()

        score.waarde = waarde
        score.save()
        return True

    # dezelfde score als voorheen --> voorlopig niet opslaan
    # (ook al is de datum en/of notitie anders)
    return False


def score_indiv_ag_opslaan(schutterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een individueel AG op voor een specifieke schutter-boog en afstand """
    return _score_ag_opslaan(SCORE_TYPE_INDIV_AG, schutterboog, afstand, gemiddelde, door_account, notitie)


def score_teams_ag_opslaan(schutterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een team-AG op voor een specifieke schutter-boog en afstand """
    return _score_ag_opslaan(SCORE_TYPE_TEAM_AG, schutterboog, afstand, gemiddelde, door_account, notitie)


def wanneer_ag_vastgesteld():
    """ Zoek de datum waarop de aanvangsgemiddelde voor het laatste vastgesteld zijn """
    scorehist = (ScoreHist
                 .objects
                 .select_related('score')
                 .filter(door_account=None,
                         score__type=SCORE_TYPE_INDIV_AG)
                 .order_by('-when'))[:1]
    if len(scorehist) > 0:
        return scorehist[0].when
    return None

# end of file
