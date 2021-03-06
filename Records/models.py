# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from NhbStructuur.models import NhbLid


DISCIPLINE = [('OD', 'Outdoor'),
              ('18', 'Indoor'),
              ('25', '25m 1pijl')]

GESLACHT = [('M', 'Man'),
            ('V', 'Vrouw')]

MATERIAALKLASSE = [('R', 'Recurve'),
                   ('C', 'Compound'),
                   ('BB', 'Barebow'),
                   ('LB', 'Longbow'),
                   ('IB', 'Instinctive bow')]

LEEFTIJDSCATEGORIE = [('M', 'Master'),
                      ('S', 'Senior'),
                      ('J', 'Junior'),
                      ('C', 'Cadet'),
                      ('U', 'Uniform (para)')]

# FUTURE: support voor team records toevoegen


class IndivRecord(models.Model):
    """ een individueel record """

    discipline = models.CharField(max_length=2, choices=DISCIPLINE)

    volg_nr = models.PositiveIntegerField()         # uniek binnen elke discipline

    soort_record = models.CharField(max_length=40)

    geslacht = models.CharField(max_length=1, choices=GESLACHT)

    leeftijdscategorie = models.CharField(max_length=1, choices=LEEFTIJDSCATEGORIE)

    materiaalklasse = models.CharField(max_length=2, choices=MATERIAALKLASSE)

    para_klasse = models.CharField(max_length=20, blank=True)

    verbeterbaar = models.BooleanField(default=True)

    nhb_lid = models.ForeignKey(NhbLid, on_delete=models.PROTECT,
                                blank=True,  # allow access input in form
                                null=True)   # allow NULL relation in database

    naam = models.CharField(max_length=50)

    datum = models.DateField()               # dates before 1950 mean "no date known"

    plaats = models.CharField(max_length=50)

    land = models.CharField(max_length=50)      # TODO: blank=True toevoegen

    score = models.PositiveIntegerField()

    x_count = models.PositiveIntegerField(default=0)

    max_score = models.PositiveIntegerField(default=0)

    score_notitie = models.CharField(max_length=30, blank=True)

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

# end of file
