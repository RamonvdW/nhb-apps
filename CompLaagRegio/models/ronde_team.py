# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Score.models import Score, ScoreHist
from .deelnemer import RegioDeelnemer
from .team import RegioTeam


class RegioRondeTeam(models.Model):

    """ Deze tabel houdt bij wat de samenstelling was van een team in een ronde van de regiocompetitie
        Bij VSG teams wordt de samenstelling aan het einde van de voorgaande ronde vastgesteld
        Bij vaste teams wordt de RegioTeam gebruikt
        Eventuele invaller kan geadministreerd worden
    """

    # over welk team gaat dit
    team = models.ForeignKey(RegioTeam, on_delete=models.CASCADE)

    # welke van de 7 rondes is dit
    ronde_nr = models.PositiveSmallIntegerField(default=0)

    # leden die (automatisch) gekoppeld zijn aan het team
    deelnemers_geselecteerd = models.ManyToManyField(RegioDeelnemer,
                                                     related_name='regiorondeteam_geselecteerd',
                                                     blank=True)

    # feitelijke leden, inclusief invallers
    deelnemers_feitelijk = models.ManyToManyField(RegioDeelnemer,
                                                  related_name='regiorondeteam_feitelijk',
                                                  blank=True)

    # gekozen scores van de feitelijke leden
    # in geval van keuze zijn deze specifiek gekozen door de RCL
    scores_feitelijk = models.ManyToManyField(Score,
                                              related_name='regiorondeteam_feitelijk',
                                              blank=True)

    # bevroren scores van de feitelijke leden op het moment dat de teamronde afgesloten werd
    scorehist_feitelijk = models.ManyToManyField(ScoreHist,
                                                 related_name='regiorondeteam_feitelijk',
                                                 blank=True)

    # beste 3 scores van leden in het team
    team_score = models.PositiveSmallIntegerField(default=0)

    # toegekende punten in deze ronde
    team_punten = models.PositiveSmallIntegerField(default=0)

    # logboek voor noteren gemiddelde van de invallers
    logboek = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "Ronde %s, team %s" % (self.ronde_nr, self.team)

    class Meta:
        verbose_name = 'Ronde team'


# end of file
