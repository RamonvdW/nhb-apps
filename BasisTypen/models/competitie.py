# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import BLAZOEN_CHOICES, BLAZOEN_40CM, BLAZOEN_60CM
from .boogtype import BoogType
from .leeftijdsklasse import Leeftijdsklasse
from .teamtype import TeamType


class TemplateCompetitieIndivKlasse(models.Model):

    """ definitie van een individuele klasse voor de volgende bondscompetities """

    # toepasselijkheid
    gebruik_18m = models.BooleanField(default=True)
    gebruik_25m = models.BooleanField(default=True)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere / oudere deelnemers
    volgorde = models.PositiveIntegerField()

    # de leeftijdsklassen: Onder 12 Jongens/Meisjes, Onder 14 Jongens/Meisjes, Onder 18, Onder 21, 21+
    leeftijdsklassen = models.ManyToManyField(Leeftijdsklasse)

    # wedstrijdklasse wel/niet meenemen naar de RK/BK
    # staat op True voor aspiranten klassen
    niet_voor_rk_bk = models.BooleanField()

    # is dit bedoeld als klasse onbekend?
    # bevat typische ook "Klasse Onbekend" in de titel
    is_onbekend = models.BooleanField(default=False)

    # is dit een klasse voor aspiranten?
    is_aspirant_klasse = models.BooleanField(default=False)

    # welke titel krijgt de hoogst geëindigde sport in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk_18m = models.CharField(max_length=30, default='Bondskampioen')
    titel_bk_25m = models.CharField(max_length=30, default='Bondskampioen')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    blazoen1_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)
    blazoen2_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    # (maar 1 keuze mogelijk)
    blazoen_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen_25m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    # niet van toepassing op de 25m1pijl
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "%s [%s]" % (self.beschrijving, self.boogtype.afkorting)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Template Competitie Indiv Klasse"
        verbose_name_plural = "Template Competitie Indiv Klassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class TemplateCompetitieTeamKlasse(models.Model):

    """ definitie van een team klasse voor de volgende bondscompetities """

    # toepasselijkheid
    gebruik_18m = models.BooleanField(default=True)
    gebruik_25m = models.BooleanField(default=True)

    # voor welk team type is deze wedstrijdklasse?
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT, null=True)

    # sorteervolgorde
    # lager nummer = betere schutters
    volgorde = models.PositiveIntegerField()

    # voorbeeld: Recurve klasse ERE
    beschrijving = models.CharField(max_length=80)

    # welke titel krijgt het hoogst geëindigde team in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk_18m = models.CharField(max_length=30, default='Bondskampioen')
    titel_bk_25m = models.CharField(max_length=30, default='Bondskampioen')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    blazoen1_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)
    blazoen2_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    blazoen_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen_25m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        msg = self.beschrijving
        if self.team_type:
            msg += ' [%s]' % self.team_type.afkorting
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Template Competitie Team Klasse"
        verbose_name_plural = "Template Competitie Team Klassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


# end of file
