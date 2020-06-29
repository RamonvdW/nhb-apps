# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import models
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid
from Account.models import Account
# mag niet afhankelijk zijn van Competitie


class SchutterNhbLidGeenEmail(Exception):
    """ Specifieke foutmelding omdat het NHB lid geen e-mail adres heeft """
    pass


class SchutterNhbLidInactief(Exception):
    """ Specifieke foutmelding omdat het NHB lid inactief is """
    pass


class SchutterVoorkeuren(models.Model):
    """ Globale voorkeuren voor een Schutter, onafhankelijk van zijn boog """

    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)

    # (opt-in) voorkeur voor DT ipv 40cm blazoen (alleen voor 18m Recurve)
    voorkeur_dutchtarget_18m = models.BooleanField(default=False)

    # (opt-out) wel/niet aanbieden om mee te doen met de competitie
    voorkeur_meedoen_competitie = models.BooleanField(default=True)

    # het account waar dit record bij hoort
    # (niet gebruiken!)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)

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

    # het account waar dit record bij hoort
    # (niet gebruiken!)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)

    # aanvangsgemiddelde is opgeslagen in een Score en ScoreHist record

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SchutterBoog"
        verbose_name_plural = "SchuttersBoog"

    def __str__(self):
        return "%s - %s" % (self.nhblid.nhb_nr, self.boogtype.beschrijving)

    objects = models.Manager()      # for the editor only


# end of file
