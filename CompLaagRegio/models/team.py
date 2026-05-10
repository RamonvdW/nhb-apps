# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import TeamType
from Competitie.models.competitie import CompetitieTeamKlasse
from Vereniging.models import Vereniging
from .regiocomp import RegioComp
from .deelnemer import RegioDeelnemer


class RegioTeam(models.Model):

    """ Een team zoals aangemaakt door de HWL van de vereniging, voor de regiocompetitie """

    # bij welke seizoen en regio hoort dit team
    regiocomp = models.ForeignKey(RegioComp, on_delete=models.CASCADE)

    # bij welke vereniging hoort dit team
    vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT)

    # een volgnummer van het team binnen de vereniging
    volg_nr = models.PositiveSmallIntegerField(default=0)

    # team type bepaalt welke boogtypen toegestaan zijn
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    # de naam van dit team (wordt getoond in plaats van team volgnummer)
    team_naam = models.CharField(max_length=50, default='')

    # initiële leden van het team
    leden = models.ManyToManyField(RegioDeelnemer,
                                   blank=True)    # mag leeg zijn

    # de berekende team sterkte / team gemiddelde
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor i.p.v. 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 30,000

    # de klasse waarin dit team ingedeeld is
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    def maak_team_naam(self):
        msg = "%s-%s" % (self.vereniging.ver_nr, self.volg_nr)
        if self.team_naam:
            msg += " (%s)" % self.team_naam
        return msg

    def maak_team_naam_kort(self):
        if self.team_naam:
            return self.team_naam
        return self.maak_team_naam()

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.maak_team_naam()

    class Meta:
        verbose_name = 'Team'

        ordering = ['vereniging__ver_nr', 'volg_nr']


# end of file
