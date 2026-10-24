# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import BLAZOEN_CHOICES, BLAZOEN_40CM
from BasisTypen.models import BoogType, Leeftijdsklasse, TeamType
from Competitie.models import Competitie


class CompetitieIndivKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen::TemplateCompetitieIndivKlasse
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere / oudere deelnemers
    volgorde = models.PositiveIntegerField()

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # de leeftijdsklassen: aspirant, cadet, junior, senior en mannen/vrouwen
    # typisch zijn twee klassen: mannen en vrouwen
    leeftijdsklassen = models.ManyToManyField(Leeftijdsklasse)

    # is dit bedoeld als klasse onbekend?
    # bevat typische ook "Klasse Onbekend" in de titel
    is_onbekend = models.BooleanField(default=False)

    # is dit een klasse voor aspiranten?
    is_aspirant_klasse = models.BooleanField(default=False)

    # wedstrijdklasse wel/niet meenemen naar de RK/BK
    # staat op False voor aspiranten klassen en klassen 'onbekend'
    is_ook_voor_rk_bk = models.BooleanField(default=False)

    # welke titel krijgt de hoogst geëindigde sport in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk = models.CharField(max_length=30, default='')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen (geen keuze)
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    # FUTURE: standaard limiet toevoegen voor elke klasse: 24

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = self.beschrijving + ' [' + self.boogtype.afkorting + '] (%.3f)' % self.min_ag
        if self.is_ook_voor_rk_bk:
            msg += ' regio+RK'
        else:
            msg += ' regio'
        return msg

    class Meta:
        verbose_name = "Competitie indiv klasse"
        verbose_name_plural = "Competitie indiv klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class CompetitieTeamKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor de teamcompetitie,
        met de vastgestelde aanvangsgemiddelden.

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen.TemplateCompetitieTeamKlasse
        en de gerefereerde TeamType wordt hierin ook plat geslagen om het aantal database accesses te begrenzen.
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # sorteervolgorde
    # lager nummer = betere sporter
    volgorde = models.PositiveIntegerField()

    # voorbeeld: Recurve klasse ERE
    beschrijving = models.CharField(max_length=80)

    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    # R/R2/C/BB/BB2/IB/TR/LB
    team_afkorting = models.CharField(max_length=3)

    # toegestane boogtypen in dit type team
    boog_typen = models.ManyToManyField(BoogType)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # voor de RK/BK teams worden nieuwe klassengrenzen vastgesteld, dus houd ze uit elkaar
    # niet van toepassing op individuele klassen
    is_voor_teams_rk_bk = models.BooleanField(default=False)

    # welke titel krijgt de hoogst geëindigde sport in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk = models.CharField(max_length=30, default='')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    # FUTURE: standaard limiet toevoegen voor elke klasse: ERE=12, rest=8

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = self.beschrijving + ' [' + self.team_afkorting + '] (%.3f)' % self.min_ag
        if self.is_voor_teams_rk_bk:
            msg += ' (RK/BK)'
        else:
            msg += ' (regio)'
        return msg

    class Meta:
        verbose_name = "Competitie team klasse"
        verbose_name_plural = "Competitie team klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


def get_competitie_indiv_leeftijdsklassen(comp: Competitie):
    lijst = list()
    pks = list()
    for klasse in (CompetitieIndivKlasse
                   .objects
                   .filter(competitie=comp)
                   .prefetch_related('leeftijdsklassen')):
        for lkl in klasse.leeftijdsklassen.all():
            if lkl.pk not in pks:
                # verwijder "Gemengd" uit de klasse beschrijving omdat dit niet relevant is voor de bondscompetitie
                lkl.beschrijving = lkl.beschrijving.replace(' Gemengd', '')
                pks.append(lkl.pk)
                tup = (lkl.volgorde, lkl.pk, lkl)
                lijst.append(tup)
        # for
    # for

    lijst.sort()        # op volgorde
    return [lkl for _, _, lkl in lijst]


# end of file
