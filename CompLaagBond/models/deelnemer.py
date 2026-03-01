# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.definities import DEELNAME_CHOICES, DEELNAME_ONBEKEND
from Competitie.models import CompetitieIndivKlasse
from .kampioenschap import KampBK
from Sporter.models import SporterBoog
from Vereniging.models import Vereniging


class DeelnemerBK(models.Model):

    """ Een sporterboog aangemeld bij een rayon- of bondskampioenschap """

    # bij welke kampioenschap hoort deze inschrijving?
    kamp = models.ForeignKey(KampBK, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # de individuele wedstrijdklasse (zelfde als voor de regio)
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     related_name='deelnemer_bk_indiv_klasse')

    # klasse die toegepast moet worden als de sporter doorstroomt naar de volgende ronde
    # initieel gelijk aan indiv_klasse
    # bij het samenvoegen van kleine klassen worden alleen indiv_klasse aangepast
    indiv_klasse_volgende_ronde = models.ForeignKey(CompetitieIndivKlasse,
                                                    on_delete=models.CASCADE,
                                                    blank=True, null=True,      # alleen nodig voor migratie
                                                    related_name='deelnemer_bk_indiv_klasse_volgende_ronde')

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
    # TODO: update fase
    # fase K: aan het begin van fase K wordt een uitnodiging gestuurd om deelname te bevestigen
    # fase K: twee weken voor begin van de wedstrijden wordt een herinnering gestuurd
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # kan deze sporter deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # gemiddelde uit de de regiocompetitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # sporters met gelijk gemiddelde moeten in de juiste volgorde gehouden worden door te kijken naar
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

    # logboek voor bijhouden aanmelden/afmelden sporter
    logboek = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        deel_str = '%s, %s, deelname=%s, rank=%s, volgorde=%s' % (self.sporterboog.boogtype.afkorting,
                                                                  self.gemiddelde,
                                                                  self.deelname,
                                                                  self.rank, self.volgorde)

        return "[%s] %s, %s" % (
                    self.sporterboog.sporter.lid_nr,
                    self.sporterboog.sporter.volledige_naam(),
                    deel_str)

    class Meta:
        verbose_name = "DeelnemerBK"
        verbose_name_plural = "DeelnemersBK"

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


# end of file
