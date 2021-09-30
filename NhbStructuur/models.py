# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from Account.models import Account
from BasisTypen.models import GESLACHT
import datetime


# global
maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID

GEBRUIK = [('18', 'Indoor'),
           ('25', '25m 1pijl')]

GEBRUIK2STR = {'18': 'Indoor',
               '25': '25m 1pijl'}


class NhbRayon(models.Model):
    """ Tabel waarin de Rayon definities """

    # 1-digit nummer van dit rayon
    rayon_nr = models.PositiveIntegerField(primary_key=True)

    # korte naam van het rayon (Rayon 1)
    naam = models.CharField(max_length=20)      # Rayon 3

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # geografisch gebied klopt niet helemaal en wordt nu niet meer getoond
        # return self.naam + ' ' + self.geografisch_gebied
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb rayon"
        verbose_name_plural = "Nhb rayons"

    objects = models.Manager()      # for the editor only


class NhbRegio(models.Model):
    """ Tabel waarin de Regio definities """

    # 3-cijferige NHB nummer van deze regio
    regio_nr = models.PositiveIntegerField(primary_key=True)

    # beschrijving van de regio
    naam = models.CharField(max_length=50)

    # rayon waar deze regio bij hoort
    rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT)

    # is dit een administratieve regio die niet mee doet voor de wedstrijden / competities?
    is_administratief = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb regio"
        verbose_name_plural = "Nhb regios"

    objects = models.Manager()      # for the source code editor only


class NhbCluster(models.Model):
    """ Tabel waarin de definitie van een cluster staat """

    # regio waar dit cluster bij hoort
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # letter voor unieke identificatie van het cluster
    letter = models.CharField(max_length=1, default='x')

    # beschrijving het cluster
    naam = models.CharField(max_length=50, default='', blank=True)

    # aparte clusters voor 18m en 25m
    gebruik = models.CharField(max_length=2, choices=GEBRUIK)

    def cluster_code(self):
        return "%s%s" % (self.regio.regio_nr, self.letter)

    def cluster_code_str(self):
        msg = "%s voor " % self.cluster_code()
        try:
            msg += GEBRUIK2STR[self.gebruik]
        except KeyError:         # pragma: no cover
            msg = "?"
        return msg

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = self.cluster_code_str()
        if self.naam:
            msg += " (%s)" % self.naam
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb cluster"
        verbose_name_plural = "Nhb clusters"

        # zorg dat elk cluster uniek is
        unique_together = ('regio', 'letter')

    objects = models.Manager()      # for the source code editor only


class NhbVereniging(models.Model):
    """ Tabel waarin gegevens van de Verenigingen van de NHB staan """

    # 4-cijferige nummer van de vereniging
    ver_nr = models.PositiveIntegerField(primary_key=True)

    # naam van de vereniging
    naam = models.CharField(max_length=200)

    # locatie van het doel van de vereniging
    plaats = models.CharField(max_length=100, blank=True)

    contact_email = models.CharField(max_length=150, blank=True)    # FUTURE: not used, can be removed

    # de regio waarin de vereniging zit
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # de optionele clusters waar deze vereniging bij hoort
    clusters = models.ManyToManyField(NhbCluster,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # wie is de secretaris van de vereniging
    # TODO: remove (replaced by Sporter.Secretaris)
    secretaris_lid = models.ForeignKey('NhbLid', on_delete=models.SET_NULL,
                                       blank=True,  # allow access input in form
                                       null=True)   # allow NULL relation in database

    # er is een vereniging voor persoonlijk lidmaatschap
    # deze leden mogen geen wedstrijden schieten
    geen_wedstrijden = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # selectie in de admin interface gaat op deze string, dus ver_nr eerst
        return "[%s] %s" % (self.ver_nr, self.naam)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb vereniging"
        verbose_name_plural = "Nhb verenigingen"

    objects = models.Manager()      # for the editor only


def validate_geboorte_datum(datum):
    """ OBSOLETE """
    return True


def validate_sinds_datum(datum):
    """ OBSOLETE """
    return True


class NhbLid(models.Model):     # TODO: needed for migration/datacopy - remove later
    """ OBSOLETE - gebruik Sporter """
    nhb_nr = models.PositiveIntegerField(primary_key=True)
    voornaam = models.CharField(max_length=100)
    achternaam = models.CharField(max_length=100)
    unaccented_naam = models.CharField(max_length=200, default='', blank=True)
    email = models.CharField(max_length=150)
    geboorte_datum = models.DateField(validators=[validate_geboorte_datum])
    geslacht = models.CharField(max_length=1, choices=GESLACHT)
    para_classificatie = models.CharField(max_length=30, blank=True)
    is_actief_lid = models.BooleanField(default=True)   # False = niet meer in import dataset
    sinds_datum = models.DateField(validators=[validate_sinds_datum])
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT, blank=True, null=True)
    lid_tot_einde_jaar = models.PositiveSmallIntegerField(default=0)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'Nhb lid'
        verbose_name_plural = 'Nhb leden'


class Speelsterkte(models.Model):       # TODO: needed for migration/datacopy - remove later
    """ OBSOLETE - vervangen door Sporter.Speelsterkte """
    lid = models.ForeignKey(NhbLid, on_delete=models.CASCADE)
    datum = models.DateField()
    beschrijving = models.CharField(max_length=50)
    discipline = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    volgorde = models.PositiveSmallIntegerField()


# end of file
