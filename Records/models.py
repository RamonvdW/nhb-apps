# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from NhbStructuur.models import NhbLid


# TODO: support voor team records toevoegen


class IndivRecord(models.Model):
    """ een individueel record """

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

    discipline = models.CharField(max_length=2, choices=DISCIPLINE)
    volg_nr = models.PositiveIntegerField()         # uniek binnen elke dicipline
    soort_record = models.CharField(max_length=40)
    geslacht = models.CharField(max_length=1, choices=GESLACHT)
    leeftijdscategorie = models.CharField(max_length=1, choices=LEEFTIJDSCATEGORIE)
    materiaalklasse = models.CharField(max_length=2, choices=MATERIAALKLASSE)
    para_klasse = models.CharField(max_length=20, blank=True)
    nhb_lid = models.ForeignKey(NhbLid, on_delete=models.PROTECT,
                                blank=True,  # allow access input in form
                                null=True)   # allow NULL relation in database
    naam = models.CharField(max_length=50)
    datum = models.DateField()               # dates before 1950 mean "no date known"
    plaats = models.CharField(max_length=50)
    land = models.CharField(max_length=50)
    score = models.PositiveIntegerField()
    x_count = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    score_notitie = models.CharField(max_length=30, blank=True)
    is_european_record = models.BooleanField(default=False)
    is_world_record = models.BooleanField(default=False)

    def __str__(self):
        return "%s: %s - %s - %s - %s - %s - %s - %s" % (self.volg_nr,
                                                         self.discipline,
                                                         self.geslacht,
                                                         self.leeftijdscategorie,
                                                         self.materiaalklasse,
                                                         self.para_klasse,
                                                         self.naam,
                                                         self.score_str())

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

    disc2str = {'OD': 'Outdoor',
                '18': 'Indoor',
                '25': '25m 1pijl'}
    gesl2str = {'M': 'Mannen',
                'V': 'Vrouwen'}
    makl2str = {'R': 'Recurve',
                'C': 'Compound',
                'BB': 'Barebow',
                'IB': 'Instinctive bow',
                'LB': 'Longbow',
                'O': 'Para klassen'}
    lcat2str = {'M': 'Masters (50+)',
                'S': 'Senioren',
                'J': 'Junioren (t/m 21 jaar)',
                'C': 'Cadetten (t/m 17 jaar)',
                'U': 'Gecombineerd (bij para)'}
    sel2str4arg = {'disc': disc2str,
                   'gesl': gesl2str,
                   'makl': makl2str,
                   'lcat': lcat2str}

    disc2url = {'OD': 'outdoor',
                '18': 'indoor',
                '25': '25m1pijl'}
    gesl2url = {'M': 'mannen',
                'V': 'vrouwen'}
    makl2url = {'R': 'recurve',
                'C': 'compound',
                'BB': 'barebow',
                'IB': 'instinctive-bow',
                'LB': 'longbow',
                'O': 'para-klassen'}
    lcat2url = {'M': 'masters',
                'S': 'senioren',
                'J': 'junioren',
                'C': 'cadetten',
                'U': 'gecombineerd'}
    sel2url4arg = {'disc': disc2url,
                   'gesl': gesl2url,
                   'makl': makl2url,
                   'lcat': lcat2url}

    url2disc = {v: k for k, v in disc2url.items()}
    url2gesl = {v: k for k, v in gesl2url.items()}
    url2makl = {v: k for k, v in makl2url.items()}
    url2lcat = {v: k for k, v in lcat2url.items()}
    url2sel4arg = {'disc': url2disc,
                   'gesl': url2gesl,
                   'makl': url2makl,
                   'lcat': url2lcat}

    objects = models.Manager()      # for the editor only


# end of file
