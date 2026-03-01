# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import TeamType
from Competitie.definities import DEELNAME_CHOICES, DEELNAME_ONBEKEND
from Competitie.models import CompetitieTeamKlasse, RegiocompetitieSporterBoog
from .kampioenschap import KampRK
from .deelnemer import DeelnemerRK
from Vereniging.models import Vereniging


class TeamRK(models.Model):

    """ Een team zoals aangemaakt door de HWL van de vereniging, voor een RK en doorstroming naar BK """

    # bij welke seizoen en RK hoort dit team?
    kamp = models.ForeignKey(KampRK, on_delete=models.CASCADE)

    # bij welke vereniging hoort dit team
    vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)

    # een volgnummer van het team binnen de vereniging
    volg_nr = models.PositiveSmallIntegerField(default=0)

    # team type bepaalt welke boogtypen toegestaan zijn
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT, null=True)

    # de naam van dit team (wordt getoond in plaats van team volgnummer)
    team_naam = models.CharField(max_length=50, default='')

    # kan dit team deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # expliciete controle of dit team een reserve is of deelnemer mag worden
    is_reserve = models.BooleanField(default=False)

    # de berekende team sterkte
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor i.p.v. 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # Positie van dit team in de lijst zoals vastgesteld aan het begin van het BK
    # dit is de originele volgorde, welke nooit meer wijzigt ook al meldt het team zich af.
    # Wordt gebruikt om het team in originele volgorde te tonen aan de BKO, inclusief afmeldingen
    # bij aanpassing van de cut kan de volgorde aangepast worden zodat kampioenen boven de cut staan
    volgorde = models.PositiveSmallIntegerField(default=0)  # inclusief afmeldingen

    # deelname positie van het team in de meest up-to-date lijst
    # de eerste N (tot de limiet/cut, standaard 8) zijn deelnemers; daarna reserve teams
    rank = models.PositiveSmallIntegerField(default=0)      # afmeldingen hebben rank 0

    # de klasse waarin dit team ingedeeld is
    # dit is preliminair tijdens het inschrijven van de teams tijdens de regiocompetitie
    # wordt op None gezet tijdens het doorzetten van de RK deelnemers (fase G)
    # wordt ingevuld na het vaststellen van de RK/BK klassengrenzen (einde fase K)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True,
                                    related_name='teamrk_team_klasse')

    # klasse die toegepast moet worden als het team doorstroomt naar de volgende ronde
    # initieel gelijk aan team_klasse
    # bij het samenvoegen van kleine klassen worden alleen team_klasse aangepast
    team_klasse_volgende_ronde = models.ForeignKey(CompetitieTeamKlasse,
                                                   on_delete=models.CASCADE,
                                                   blank=True, null=True,
                                                   related_name='teamrk_team_klasse_volgende_ronde')

    # preliminaire leden van het team (gekozen tijdens de regiocompetitie)
    tijdelijke_leden = models.ManyToManyField(RegiocompetitieSporterBoog,
                                              related_name='teamrk_tijdelijke_leden',
                                              blank=True)    # mag leeg zijn

    # de voor het kampioenschap geplaatste sporters die ook lid zijn van het team
    gekoppelde_leden = models.ManyToManyField(DeelnemerRK,
                                              related_name='teamrk_gekoppelde_leden',
                                              blank=True)   # mag leeg zijn

    # de feitelijke sporters die tijdens de kampioenschappen in het team stonden (invallers)
    feitelijke_leden = models.ManyToManyField(DeelnemerRK,
                                              related_name='teamrk_feitelijke_leden',
                                              blank=True)   # mag leeg zijn

    # kampioenschap uitslag: score en ranking
    # volgorde wordt gebruikt om binnen plek 5 en 9 de volgorde vast te houden
    result_rank = models.PositiveSmallIntegerField(default=0)               # 100=blanco, 32000=no show, 32001=reserve
    result_volgorde = models.PositiveSmallIntegerField(default=0)

    # teamscore is het aantal matchpunten (max 14, bij 7 wedstrijdjes)
    result_teamscore = models.PositiveSmallIntegerField(default=0)                  # max = 32767
    result_shootoff_str = models.CharField(max_length=20, default='', blank=True)   # "(SO: 27)"

    class Meta:
        verbose_name = "TeamRK"
        verbose_name_plural = "TeamsRK"

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        afk = self.team_type.afkorting if self.team_type else '?'
        return "%s: %s (teamtype=%s, deelname=%s, rank=%s, volgorde=%s)" % (self.vereniging,
                                                                            self.team_naam,
                                                                            afk,
                                                                            self.deelname,
                                                                            self.rank,
                                                                            self.volgorde)


# end of file
