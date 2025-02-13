# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import TeamType
from Competitie.definities import (DEEL_BK, DEEL_RK,
                                   DEELNAME_CHOICES, DEELNAME_ONBEKEND)
from Competitie.models.competitie import Competitie, CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.models.laag_regio import RegiocompetitieSporterBoog
from Functie.models import Functie
from Geo.models import Rayon
from Sporter.models import SporterBoog
from Vereniging.models import Vereniging


class Kampioenschap(models.Model):
    """ Deze tabel bevat informatie over een deel van de kampioenschappen 4xRK / 1xBK en Indiv/Teams:
    """
    DEEL = [(DEEL_RK, 'RK'),
            (DEEL_BK, 'BK')]

    deel = models.CharField(max_length=2, choices=DEEL)

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # rayon, voor RK
    rayon = models.ForeignKey(Rayon, on_delete=models.PROTECT,
                              null=True, blank=True)    # optioneel want alleen voor RK

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    # wedstrijden
    rk_bk_matches = models.ManyToManyField(CompetitieMatch, blank=True)

    # heeft deze RK/BK al een vastgestelde deelnemerslijst?
    heeft_deelnemerslijst = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        deel2str = {code: beschrijving for code, beschrijving in self.DEEL}
        msg = deel2str[self.deel]
        if self.rayon:
            msg += ' Rayon %s' % self.rayon.rayon_nr
        return msg

    class Meta:
        verbose_name = "Kampioenschap"
        verbose_name_plural = "Kampioenschappen"

    objects = models.Manager()      # for the editor only


class KampioenschapIndivKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal deelnemers in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welk kampioenschap (i.v.m. scheiding RKs)
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse, on_delete=models.CASCADE)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s - %s: %s" % (self.kampioenschap, self.indiv_klasse.beschrijving, self.limiet)

    class Meta:
        verbose_name = "Kampioenschap IndivKlasse Limiet"
        verbose_name_plural = "Kampioenschap IndivKlasse Limieten"


class KampioenschapTeamKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal teams in een RK of BK
        wedstrijdklasse. De RKO/BKO kan dit bijstellen specifiek voor zijn kampioenschap.
    """

    # voor welk kampioenschap (i.v.m. scheiding RKs)
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    team_klasse = models.ForeignKey(CompetitieTeamKlasse, on_delete=models.CASCADE)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "%s : " % self.limiet
        msg += "%s - " % self.team_klasse.beschrijving
        msg += "%s" % self.kampioenschap
        return msg

    class Meta:
        verbose_name = "Kampioenschap TeamKlasse Limiet"
        verbose_name_plural = "Kampioenschap TeamKlasse Limieten"


class KampioenschapSporterBoog(models.Model):

    """ Een sporterboog aangemeld bij een rayon- of bondskampioenschap """

    # bij welke kampioenschap hoort deze inschrijving?
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # de individuele wedstrijdklasse (zelfde als voor de regio)
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE)

    # klasse die toegepast moet worden als de sporter doorstroomt naar de volgende ronde
    # initieel gelijk aan indiv_klasse
    # bij het samenvoegen van kleine klassen worden alleen indiv_klasse aangepast
    indiv_klasse_volgende_ronde = models.ForeignKey(CompetitieIndivKlasse,
                                                    on_delete=models.CASCADE,
                                                    blank=True, null=True,      # alleen nodig voor migratie
                                                    related_name='indiv_klasse_volgende_ronde')

    # vereniging wordt hier apart bijgehouden omdat leden over kunnen stappen
    # tijdens het seizoen.
    # Tijdens fase G wordt de vereniging bevroren voor het RK.
    bij_vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                       blank=True, null=True)

    # kampioenen hebben een label
    kampioen_label = models.CharField(max_length=50, default='', blank=True)

    # Positie van deze sporter in de lijst zoals vastgesteld aan het begin van het RK/BK.
    # Dit is de originele volgorde, welke nooit meer wijzigt ook al meldt de sporter zich af.
    # Wordt gebruikt om de sporters in originele volgorde te tonen aan de RKO/BKO, inclusief afmeldingen.
    # Bij aanpassing van de cut kan de volgorde aangepast worden zodat kampioenen boven de cut staan
    volgorde = models.PositiveSmallIntegerField(default=0)  # inclusief afmeldingen

    # deelname positie van de sporter in de meest up-to-date lijst
    # de eerste N (tot de limiet/cut, standaard 24) zijn deelnemers; daarna reserve sporters
    rank = models.PositiveSmallIntegerField(default=0)      # afmeldingen hebben rank 0

    # wanneer hebben we een bevestiging gevraagd hebben via e-mail
    # fase K: aan het begin van fase K wordt een uitnodiging gestuurd om deelname te bevestigen
    # fase K: twee weken voor begin van de wedstrijden wordt een herinnering gestuurd
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # kan deze sporter deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # gemiddelde uit de voorgaande regiocompetitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # sporters met gelijk gemiddelde moeten in de juiste volgorde gehouden worden door te kijken naar
    # de regio scores: hoogste score gaat voor
    # de RK scores: hoogste score gaat voor
    # scores zijn als string opgeslagen zodat er gesorteerd kan worden
    # noqa "AAABBBCCCDDDEEEFFFGGG" met AAA..GGG=7 scores van 3 cijfers, gesorteerd van beste naar slechtste score
    gemiddelde_scores = models.CharField(max_length=24, default='', blank=True)

    # resultaat van het individuele kampioenschap
    result_score_1 = models.PositiveSmallIntegerField(default=0)                # max = 32767
    result_score_2 = models.PositiveSmallIntegerField(default=0)
    result_counts = models.CharField(max_length=20, default='', blank=True)     # 25m1pijl: 5x10 3x9

    # 0 = niet meegedaan (default)
    # 1..24 = plaats op RK deelnemer, voor zover bekend
    # KAMP_RANK_RESERVE = niet afgemeld, reserve, niet meegedaan
    # KAMP_RANK_NO_SHOW = niet afgemeld, wel uitgenodigd, niet meegedaan. Waarschijnlijk een no-show.
    result_rank = models.PositiveSmallIntegerField(default=0)
    result_volgorde = models.PositiveSmallIntegerField(default=99)   # gesorteerde uitslag, inclusief alle 5e plekken

    # individuele RK deelnemer wordt gekoppeld aan de RK/BK teams
    # scores worden hier bijgehouden

    # resultaat van de RK teams deelname van deze sporter
    result_rk_teamscore_1 = models.PositiveSmallIntegerField(default=0)         # max = 32767
    result_rk_teamscore_2 = models.PositiveSmallIntegerField(default=0)

    # resultaat van de BK teams deelname van deze sporter
    result_bk_teamscore_1 = models.PositiveSmallIntegerField(default=0)         # max = 32767
    result_bk_teamscore_2 = models.PositiveSmallIntegerField(default=0)

    # logboek voor bijhouden aanmelden/afmelden sporter
    logboek = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.kampioenschap.deel == DEEL_BK:
            deel_str = "BK"
        else:
            deel_str = "RK rayon %s" % self.kampioenschap.rayon.rayon_nr

        deel_str += ' (deelname=%s, rank=%s, volgorde=%s)' % (self.deelname, self.rank, self.volgorde)

        return "[%s] %s (%s) %s" % (
                    self.sporterboog.sporter.lid_nr,
                    self.sporterboog.sporter.volledige_naam(),
                    self.sporterboog.boogtype.beschrijving,
                    deel_str)

    class Meta:
        verbose_name = "Kampioenschap sporterboog"
        verbose_name_plural = "Kampioenschap sportersboog"

        indexes = [
            # help sorteren op gemiddelde (hoogste eerst)
            models.Index(fields=['-gemiddelde']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),

            # help sorteren op rank
            models.Index(fields=['rank']),

            # help sorteren op volgorde en gemiddelde
            models.Index(fields=['volgorde', '-gemiddelde']),
        ]

    objects = models.Manager()      # for the editor only


class KampioenschapTeam(models.Model):
    """ Een team zoals aangemaakt door de HWL van de vereniging, voor een RK en doorstroming naar BK """

    # bij welke seizoen en RK hoort dit team?
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)        # nodig voor de migratie

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

    # kampioenen hebben een label
    rk_kampioen_label = models.CharField(max_length=50, default='', blank=True)

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
                                    blank=True, null=True)

    # klasse die toegepast moet worden als het team doorstroomt naar de volgende ronde
    # initieel gelijk aan team_klasse
    # bij het samenvoegen van kleine klassen worden alleen team_klasse aangepast
    team_klasse_volgende_ronde = models.ForeignKey(CompetitieTeamKlasse,
                                                   on_delete=models.CASCADE,
                                                   blank=True, null=True,
                                                   related_name='team_klasse_volgende_ronde')

    # preliminaire leden van het team (gekozen tijdens de regiocompetitie)
    tijdelijke_leden = models.ManyToManyField(RegiocompetitieSporterBoog,
                                              related_name='kampioenschapteam_tijdelijke_leden',
                                              blank=True)    # mag leeg zijn

    # de voor het kampioenschap geplaatste sporters die ook lid zijn van het team
    gekoppelde_leden = models.ManyToManyField(KampioenschapSporterBoog,
                                              related_name='kampioenschapteam_gekoppelde_leden',
                                              blank=True)   # mag leeg zijn

    # de feitelijke sporters die tijdens de kampioenschappen in het team stonden (invallers)
    feitelijke_leden = models.ManyToManyField(KampioenschapSporterBoog,
                                              related_name='kampioenschapteam_feitelijke_leden',
                                              blank=True)   # mag leeg zijn

    # kampioenschap uitslag: score en ranking
    # volgorde wordt gebruikt om binnen plek 5 en 9 de volgorde vast te houden
    result_rank = models.PositiveSmallIntegerField(default=0)
    result_volgorde = models.PositiveSmallIntegerField(default=0)

    result_teamscore = models.PositiveSmallIntegerField(default=0)          # max = 32767

    result_counts = models.CharField(max_length=20, default='', blank=True)     # 25m1pijl: 5x10 3x9

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s: %s (deelname=%s, rank=%s, volgorde=%s)" % (self.vereniging,
                                                               self.team_naam,
                                                               self.deelname,
                                                               self.rank,
                                                               self.volgorde)

# end of file
