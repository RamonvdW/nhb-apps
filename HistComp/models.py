# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


class HistCompetitie(models.Model):
    """ Deze database tabel bevat een overzicht van alle historische competities.
        De gebruiker kan een eerste keuze maken uit een lijst die uit deze tabel komt.

        De tabel bevat velden die anders heel vaak herhaald zouden worden in een andere tabel
        en het voorkomt zoeken naar deze informatie uit de grote tabel.
    """
    COMP_TYPE = [('18', '18m Indoor'),      # note: 18, 25 must be in sync with Competitie.AFSTAND
                 ('25', '25m1pijl')]

    comptype2str = {'18': '18m Indoor',
                    '25': '25m 1pijl'}

    # primary key = los uniek nummer
    seizoen = models.CharField(max_length=9)          # 20xx/20yy
    comp_type = models.CharField(max_length=2, choices=COMP_TYPE)  # 18/25
    klasse = models.CharField(max_length=20)          # Recurve / Compound
    is_team = models.BooleanField(default=False)

    # TODO: voeg vertaaltabellen toe voor klasse2url en url2klasse (zie records)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s (%s) %s (team=%s)" % (self.seizoen,
                                         self.comp_type,
                                         self.klasse,
                                         self.is_team)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Historie competitie"

    objects = models.Manager()      # for the editor only


class HistCompetitieIndividueel(models.Model):
    """ Deze database tabel bevat alle resultaten van de individuele competitie
        Per regel: subklasse, rank, schutter details, scores en gemiddelde.
    """
    # primary key = los uniek nummer
    histcompetitie = models.ForeignKey(HistCompetitie, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField()
    schutter_nr = models.PositiveIntegerField()             # NHB nummer
    schutter_naam = models.CharField(max_length=50)         # voor + achternaam aaneen
    boogtype = models.CharField(max_length=5,               # R/C/BB/IB/LB
                                null=True, blank=True)      # indien beschikbaar
    vereniging_nr = models.PositiveIntegerField()           # NHB nummer
    vereniging_naam = models.CharField(max_length=50)
    score1 = models.PositiveIntegerField()
    score2 = models.PositiveIntegerField()
    score3 = models.PositiveIntegerField()
    score4 = models.PositiveIntegerField()
    score5 = models.PositiveIntegerField()
    score6 = models.PositiveIntegerField()
    score7 = models.PositiveIntegerField()
    laagste_score_nr = models.PositiveIntegerField(default=0)  # 1..7
    totaal = models.PositiveIntegerField()
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s, %s" % (self.rank, self.schutter_nr)

    class Meta:
        """ meta data voor de admin interface """
        # TODO: Historie --> Historische
        verbose_name = verbose_name_plural = "Historie individuele competitie"

    objects = models.Manager()      # for the editor only


class HistCompetitieTeam(models.Model):
    """ Deze database tabel bevat alle resultaten van de teamcompetitie
        Per regel: subklasse, rank, schutter details, scores en gemiddelde.
    """
    # primary key = los uniek nummer
    histcompetitie = models.ForeignKey(HistCompetitie, on_delete=models.CASCADE)
    subklasse = models.CharField(max_length=20)         # ERE / A
    rank = models.PositiveIntegerField()
    vereniging_nr = models.PositiveIntegerField()       # NHB nummer
    vereniging_naam = models.CharField(max_length=50)
    team_nr = models.PositiveSmallIntegerField()
    totaal_ronde1 = models.PositiveIntegerField()
    totaal_ronde2 = models.PositiveIntegerField()
    totaal_ronde3 = models.PositiveIntegerField()
    totaal_ronde4 = models.PositiveIntegerField()
    totaal_ronde5 = models.PositiveIntegerField()
    totaal_ronde6 = models.PositiveIntegerField()
    totaal_ronde7 = models.PositiveIntegerField()
    totaal = models.PositiveIntegerField()
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=1)    # 1000.0

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s, %s, %s" % (self.subklasse,
                               self.rank,
                               self.vereniging_nr)

    class Meta:
        """ meta data voor de admin interface """
        # TODO: Historie --> Historische
        verbose_name = verbose_name_plural = "Historie team competitie"

    objects = models.Manager()      # for the editor only


# end of file
