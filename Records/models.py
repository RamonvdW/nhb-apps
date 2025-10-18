# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Records.definities import DISCIPLINE, GESLACHT, LEEFTIJDSCATEGORIE, MATERIAALKLASSE
from Sporter.models import Sporter


# FUTURE: support voor team records toevoegen


class IndivRecord(models.Model):
    """ een individueel record """

    # een uniek volgnummer (komt uit de administratie van de records)
    # moet uniek zijn binnen elke discipline
    # wordt ook gebruikt voor de permanente url
    volg_nr = models.PositiveIntegerField()

    # indoor, outdoor, 25m1p
    discipline = models.CharField(max_length=2, choices=DISCIPLINE)

    soort_record = models.CharField(max_length=40)

    # man of vrouw
    geslacht = models.CharField(max_length=1, choices=GESLACHT)

    # cadet, junior, senior, etc.
    leeftijdscategorie = models.CharField(max_length=1, choices=LEEFTIJDSCATEGORIE)

    # compound, recurve, etc.
    materiaalklasse = models.CharField(max_length=2, choices=MATERIAALKLASSE)

    para_klasse = models.CharField(max_length=20, blank=True)

    # is het record verbeterbaar?
    verbeterbaar = models.BooleanField(default=True)

    # sporter waar dit record bij hoort
    # (niet voor alle records beschikbaar)
    sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT, blank=True, null=True)

    # naam van de recordhouder
    naam = models.CharField(max_length=50)

    # wanneer is het record geschoten?
    datum = models.DateField()               # dates before 1950 mean "no date known"

    # waar is het record geschoten?
    plaats = models.CharField(max_length=50)
    land = models.CharField(max_length=50, blank=True)

    # wat was de score?
    score = models.PositiveIntegerField()
    x_count = models.PositiveIntegerField(default=0)

    # wat is het maximum?
    max_score = models.PositiveIntegerField(default=0)

    # eventuele notities
    score_notitie = models.CharField(max_length=30, blank=True)

    # was het toen een Europees of wereld record?
    is_european_record = models.BooleanField(default=False)
    is_world_record = models.BooleanField(default=False)

    def __str__(self):
        return "%s: %s - %s - %s%s%s - %s - %s - %s - %s - %s" % (
                    self.volg_nr,
                    self.discipline,
                    self.soort_record,
                    self.materiaalklasse,
                    self.leeftijdscategorie,
                    self.geslacht,
                    self.para_klasse,
                    self.naam,
                    self.score_str(),
                    self.datum,
                    self.plaats)

    def score_str(self):
        """  make score beschrijving, inclusief X-count indien relevant """
        msg = str(self.score)
        if self.x_count:
            msg += " (%sX)" % self.x_count
        return msg

    def max_score_str(self):
        msg = "%s" % self.max_score
        if self.x_count:
            # add maximum X-count to maximum score
            max_x_count = int(self.max_score / 10)
            msg += " (%sX)" % max_x_count
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Individueel record"
        verbose_name_plural = "Individuele records"

    objects = models.Manager()      # for the editor only


class BesteIndivRecords(models.Model):

    """ Het beste individuele record dat nog verbeterbaar is
        deze wordt bijgewerkt tijdens elke import
    """

    # presentatie-volgorde
    volgorde = models.PositiveIntegerField(default=0)

    # de unieke combi van een record type
    discipline = models.CharField(max_length=2, choices=DISCIPLINE)
    soort_record = models.CharField(max_length=40)
    geslacht = models.CharField(max_length=1, choices=GESLACHT)
    leeftijdscategorie = models.CharField(max_length=1, choices=LEEFTIJDSCATEGORIE)
    materiaalklasse = models.CharField(max_length=2, choices=MATERIAALKLASSE)
    para_klasse = models.CharField(max_length=20, blank=True)

    # het beste record in bovenstaande klasse
    # optioneel, zodat ook klassen zonder records toegevoegd kunnen worden
    beste = models.ForeignKey(IndivRecord, on_delete=models.SET_NULL,
                              null=True, blank=True)

    def __str__(self):
        return "(%s) %s - %s - %s - %s - %s - %s - %s" % (self.pk,
                                                          self.volgorde,
                                                          self.discipline,
                                                          self.soort_record,
                                                          self.geslacht,
                                                          self.leeftijdscategorie,
                                                          self.materiaalklasse,
                                                          self.para_klasse)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Beste individuele records"


class AnderRecord(models.Model):

    """ vrij-formaat rapport met een referentie naar een nieuwsbericht """

    # controleer volgorde waarin de artikelen getoond worden: voor hoog (=nieuwste = vooraan) naar laag
    volgorde = models.PositiveSmallIntegerField(default=0)

    # titel van het kaartje
    titel = models.CharField(max_length=30)

    # icoon van het kaartje
    sv_icon = models.CharField(max_length=20)

    # tekst voor op het kaartje
    tekst = models.CharField(max_length=100)

    # URL naar het nieuwsbericht
    url = models.CharField(max_length=100)

    # publicatiedatum
    datum = models.DateField(default='2000-01-01')

    def __str__(self):
        return "[%s] %s" % (self.volgorde, self.titel)

    class Meta:
        verbose_name = 'Ander record'
        verbose_name_plural = 'Andere records'


# end of file
