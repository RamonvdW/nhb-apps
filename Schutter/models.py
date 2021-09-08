# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid
# mag niet afhankelijk zijn van Competitie


class SchutterNhbLidGeenEmail(Exception):
    """ Specifieke foutmelding omdat het NHB lid geen e-mail adres heeft """

    def __init__(self, nhblid):
        self.nhblid = nhblid


class SchutterNhbLidInactief(Exception):
    """ Specifieke foutmelding omdat het NHB lid inactief is """
    pass


class SchutterVoorkeuren(models.Model):
    """ Globale voorkeuren voor een Schutter, onafhankelijk van zijn boog """

    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)

    # (opt-in) voorkeur voor eigen blazoen: Dutch Target (Recurve) of 60cm 4spot (Compound)
    voorkeur_eigen_blazoen = models.BooleanField(default=False)

    # (opt-out) wel/niet aanbieden om mee te doen met de competitie
    voorkeur_meedoen_competitie = models.BooleanField(default=True)

    # sporters met para-classificatie mogen een opmerking toevoegen voor de wedstrijdleiding
    opmerking_para_sporter = models.CharField(max_length=256, default='')

    # (opt-out) voorkeur voor wedstrijden van specifieke disciplines
    voorkeur_discipline_25m1pijl = models.BooleanField(default=True)
    voorkeur_discipline_outdoor = models.BooleanField(default=True)
    voorkeur_discipline_indoor = models.BooleanField(default=True)      # Indoor = 18m/25m 3pijl
    voorkeur_discipline_clout = models.BooleanField(default=True)
    voorkeur_discipline_veld = models.BooleanField(default=True)
    voorkeur_discipline_run = models.BooleanField(default=True)
    voorkeur_discipline_3d = models.BooleanField(default=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Schutter voorkeuren"

    def __str__(self):
        return "%s" % self.nhblid.nhb_nr

    objects = models.Manager()      # for the editor only


class SchutterBoog(models.Model):
    """ Schutter met een specifiek type boog en zijn voorkeuren
        voor elk type boog waar de schutter interesse in heeft is er een entry
    """
    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)

    # voorkeuren van de schutter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    # aanvangsgemiddelde is opgeslagen in een Score en ScoreHist record

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SchutterBoog"
        verbose_name_plural = "SchuttersBoog"

    def __str__(self):
        # voorkom exceptie als nhblid op None staat
        if self.nhblid:
            return "%s - %s" % (self.nhblid.nhb_nr, self.boogtype.beschrijving)
        else:
            # komt voor als we een fake ScoreHist record aanmaken om de background task te triggeren
            return "lid? - %s" % self.boogtype.beschrijving

    objects = models.Manager()      # for the editor only


# end of file
