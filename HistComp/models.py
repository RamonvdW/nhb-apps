# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from decimal import Decimal
from HistComp.definities import HISTCOMP_RK, HISTCOMP_BK, HISTCOMP_CHOICES_RK_BK, HISTCOMP_TYPE, HISTCOMP_TYPE2STR


class HistCompSeizoen(models.Model):
    """ Seizoen """

    # 20xx/20yy (yy = xx+1)
    seizoen = models.CharField(max_length=9)

    # '18' = 18m = Indoor
    # '25' = 25m = 25m1pijl
    comp_type = models.CharField(max_length=2, choices=HISTCOMP_TYPE)

    # beste aantal scores waarover het regio gemiddelde berekend is
    # normaal 6, maar in de corona-jaren is dit verlaagd geweest naar 5
    aantal_beste_scores = models.PositiveSmallIntegerField(default=6)

    # is deze al openbaar?
    # staat op True als de huidige competitie nog loopt, maar de eindstand van de regiocompetitie
    # alvast overgezet is i.v.m. berekenen nieuwe AG's
    is_openbaar = models.BooleanField(default=True)

    # voor het presenteren van de kaartjes: zijn gegevens beschikbaar voor RK en BK uitslag?
    heeft_uitslag_rk_indiv = models.BooleanField(default=False)
    heeft_uitslag_bk_indiv = models.BooleanField(default=False)

    heeft_uitslag_regio_teams = models.BooleanField(default=False)
    heeft_uitslag_rk_teams = models.BooleanField(default=False)
    heeft_uitslag_bk_teams = models.BooleanField(default=False)

    # lijst van boog afkortingen, gescheiden door een komma
    # voorbeeld: R,C,BB,TR,LB
    indiv_bogen = models.CharField(max_length=20)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        try:
            type_str = HISTCOMP_TYPE2STR[self.comp_type]
        except KeyError:
            type_str = '?'
        msg = "Seizoen %s: %s" % (self.seizoen, type_str)
        return msg

    class Meta:
        """ meta data voor de admin interface """
        ordering = ['seizoen', 'comp_type']
        verbose_name = "Hist seizoen"
        verbose_name_plural = "Hist seizoenen"

    objects = models.Manager()      # for the editor only


class HistCompRegioIndiv(models.Model):
    """ Deze database tabel bevat alle resultaten van de individuele competitie
        Per regel: subklasse, rank, schutter details, scores en gemiddelde.
    """

    seizoen = models.ForeignKey(HistCompSeizoen, on_delete=models.CASCADE)

    # individuele wedstrijdklasse
    # voorbeeld: Compound Onder 21 klasse onbekend
    klasse_indiv = models.CharField(max_length=35, default='')      # TODO: remove default

    # volgorde in de vastgestelde uitslag in deze wedstrijdklasse
    rank = models.PositiveSmallIntegerField()

    # lid nummer en volledige naam
    sporter_lid_nr = models.PositiveIntegerField()
    sporter_naam = models.CharField(max_length=50)

    # R/C/BB/IB/LB/TR
    boogtype = models.CharField(max_length=5, default='')

    # vereniging van de sporter (bij afsluiten competitie)
    vereniging_nr = models.PositiveSmallIntegerField()
    vereniging_naam = models.CharField(max_length=50)
    vereniging_plaats = models.CharField(max_length=35, default='')
    regio_nr = models.PositiveSmallIntegerField(default=0)

    # de regio scores
    score1 = models.PositiveSmallIntegerField(default=0)
    score2 = models.PositiveSmallIntegerField(default=0)
    score3 = models.PositiveSmallIntegerField(default=0)
    score4 = models.PositiveSmallIntegerField(default=0)
    score5 = models.PositiveSmallIntegerField(default=0)
    score6 = models.PositiveSmallIntegerField(default=0)
    score7 = models.PositiveSmallIntegerField(default=0)

    # welke score doorstrepen?
    laagste_score_nr = models.PositiveSmallIntegerField(default=0)  # 1..7

    # som van de beste 6 scores
    totaal = models.PositiveSmallIntegerField()

    # gemiddelde pijl (10.000) = totaal / aantal niet-nul scores
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "rank %s: %s [%s] %s, %s" % (self.rank, self.gemiddelde,
                                            self.sporter_lid_nr, self.sporter_naam,
                                            self.boogtype)

    def tel_aantal_scores(self):
        count = 0
        nul = Decimal('0.000')
        for score in (self.score1,
                      self.score2,
                      self.score3,
                      self.score4,
                      self.score5,
                      self.score6,
                      self.score7):
            if score > nul:
                count += 1
        # for
        return count

    class Meta:
        """ meta data voor de admin interface """
        ordering = ['rank']
        verbose_name = verbose_name_plural = "Hist regio indiv"

    objects = models.Manager()      # for the editor only


class HistCompRegioTeam(models.Model):
    """ Deze database tabel bevat alle resultaten van de teamcompetitie
        Per regel: subklasse, rank, schutter details, scores en gemiddelde.
    """

    seizoen = models.ForeignKey(HistCompSeizoen, on_delete=models.CASCADE)

    # voorbeeld: Traditional klasse ERE
    team_klasse = models.CharField(max_length=30)

    # verenigingsnummer en volledige naam
    # omdat de naam meerdere keren voorkomt is ook de plaats nodig
    vereniging_nr = models.PositiveSmallIntegerField()
    vereniging_naam = models.CharField(max_length=50)
    vereniging_plaats = models.CharField(max_length=35)
    regio_nr = models.PositiveSmallIntegerField()

    # vereniging kan meerdere teams hebben
    # team naam wordt niet opgeslagen, omdat het meestal een rommeltje is
    team_nr = models.PositiveSmallIntegerField()

    rank = models.PositiveSmallIntegerField(default=0)

    # score en punten per ronde
    ronde_1_score = models.PositiveSmallIntegerField(default=0)
    ronde_2_score = models.PositiveSmallIntegerField(default=0)
    ronde_3_score = models.PositiveSmallIntegerField(default=0)
    ronde_4_score = models.PositiveSmallIntegerField(default=0)
    ronde_5_score = models.PositiveSmallIntegerField(default=0)
    ronde_6_score = models.PositiveSmallIntegerField(default=0)
    ronde_7_score = models.PositiveSmallIntegerField(default=0)

    ronde_1_punten = models.PositiveSmallIntegerField(default=0)
    ronde_2_punten = models.PositiveSmallIntegerField(default=0)
    ronde_3_punten = models.PositiveSmallIntegerField(default=0)
    ronde_4_punten = models.PositiveSmallIntegerField(default=0)
    ronde_5_punten = models.PositiveSmallIntegerField(default=0)
    ronde_6_punten = models.PositiveSmallIntegerField(default=0)
    ronde_7_punten = models.PositiveSmallIntegerField(default=0)

    # totale score en punten
    totaal_score = models.PositiveSmallIntegerField(default=0)
    totaal_punten = models.PositiveSmallIntegerField(default=0)

    # team leden worden niet bijgehouden voor de regiocompetitie omdat het geen aparte scores zijn

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "rank %s: %s / %s [%s] %s, %s" % (self.rank, self.totaal_score, self.totaal_punten,
                                                 self.vereniging_nr, self.team_nr,
                                                 self.team_klasse)

    class Meta:
        """ meta data voor de admin interface """
        ordering = ['rank', 'team_klasse']
        verbose_name = verbose_name_plural = "Hist regio teams"

    objects = models.Manager()      # for the editor only


class HistKampIndiv(models.Model):

    seizoen = models.ForeignKey(HistCompSeizoen, on_delete=models.CASCADE)

    # individuele wedstrijdklasse
    # voorbeeld: Compound Onder 21 klasse 2
    # noteer: aspiranten kunnen in de RK uitkomen in een andere klasse
    klasse_indiv = models.CharField(max_length=35)

    # lid nummer en volledige naam
    sporter_lid_nr = models.PositiveIntegerField()
    sporter_naam = models.CharField(max_length=50)

    # R/C/BB/IB/LB/TR
    boogtype = models.CharField(max_length=5)

    # vereniging van de sporter (bij afsluiten competitie)
    vereniging_nr = models.PositiveSmallIntegerField()
    vereniging_naam = models.CharField(max_length=50)
    vereniging_plaats = models.CharField(max_length=35, default='')
    rayon_nr = models.PositiveSmallIntegerField()

    # volgorde in de vastgestelde uitslag in deze wedstrijdklasse
    rank_rk = models.PositiveSmallIntegerField()
    rank_bk = models.PositiveSmallIntegerField(default=0)            # 0 = niet meegedaan

    rk_score_is_blanco = models.BooleanField(default=False)
    rk_score_1 = models.PositiveSmallIntegerField(default=0)
    rk_score_2 = models.PositiveSmallIntegerField(default=0)

    bk_score_1 = models.PositiveSmallIntegerField(default=0)
    bk_score_2 = models.PositiveSmallIntegerField(default=0)

    # bijdrage aan de het rk/bk teams
    teams_rk_score_1 = models.PositiveSmallIntegerField(default=0)
    teams_rk_score_2 = models.PositiveSmallIntegerField(default=0)

    teams_bk_score_1 = models.PositiveSmallIntegerField(default=0)
    teams_bk_score_2 = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] %s, %s" % (self.sporter_lid_nr, self.sporter_naam, self.boogtype)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Hist rk/bk indiv"

    objects = models.Manager()      # for the editor only


class HistKampTeam(models.Model):
    """ Deze database tabel bevat de resultaten van de RK en BK voor de teamcompetitie
    """

    seizoen = models.ForeignKey(HistCompSeizoen, on_delete=models.CASCADE)

    rk_of_bk = models.CharField(max_length=1, choices=HISTCOMP_CHOICES_RK_BK, default=HISTCOMP_RK)

    # voorbeeld: Traditional klasse ERE
    klasse_teams = models.CharField(max_length=30)

    # verenigingsnummer en volledige naam
    # omdat de naam meerdere keren voorkomt is ook de plaats nodig
    vereniging_nr = models.PositiveSmallIntegerField()
    vereniging_naam = models.CharField(max_length=50)
    vereniging_plaats = models.CharField(max_length=35, default='')

    # vereniging kan meerdere teams hebben
    # team naam wordt niet opgeslagen, omdat het meestal een rommeltje is
    team_nr = models.PositiveSmallIntegerField()

    # behaalde score en rank
    team_score = models.PositiveSmallIntegerField()
    rank = models.PositiveSmallIntegerField()

    # wie schoten voor dit team: geeft lid nummer, naam en boog
    # deze sporters waren ook voor het RK geplaatst
    lid_1 = models.ForeignKey(HistKampIndiv, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name='team_lid_1')
    lid_2 = models.ForeignKey(HistKampIndiv, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name='team_lid_2')
    lid_3 = models.ForeignKey(HistKampIndiv, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name='team_lid_3')
    lid_4 = models.ForeignKey(HistKampIndiv, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name='team_lid_4')

    # bijdrage van elk team lid, van hoogste naar laagste score
    score_lid_1 = models.PositiveSmallIntegerField(default=0)
    score_lid_2 = models.PositiveSmallIntegerField(default=0)
    score_lid_3 = models.PositiveSmallIntegerField(default=0)
    score_lid_4 = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s: %s - %s (%s)" % (self.rank, self.vereniging_nr, self.team_nr, self.team_score)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Hist rk/bk teams"

    objects = models.Manager()      # for the editor only


# end of file
