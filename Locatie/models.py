# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Locatie.definities import BAAN_TYPE_ONBEKEND, BAAN_TYPE, BAANTYPE2STR
from Vereniging.models import Vereniging


class Locatie(models.Model):
    """ Een locatie waarop een wedstrijd of cursus gehouden kan worden.

        Naast de accommodatie van de vereniging (binnen / buiten) ook externe locaties
        waar de vereniging een wedstrijd/cursus kan organiseren.
    """

    # naam waaronder deze locatie getoond wordt
    naam = models.CharField(max_length=50, blank=True)

    # zichtbaar maakt het mogelijk een baan uit het systeem te halen
    # zonder deze helemaal te verwijderen
    zichtbaar = models.BooleanField(default=True)

    # verenigingen die deze locatie gebruiken (kan gedeeld doel zijn)
    verenigingen = models.ManyToManyField(Vereniging)

    # eigen accommodatie binnenbaan (volledig overdekt of half overdekt), buitenbaan, extern of 'onbekend'
    baan_type = models.CharField(max_length=1, choices=BAAN_TYPE, default=BAAN_TYPE_ONBEKEND)

    # welke disciplines kunnen hier georganiseerd worden?
    discipline_25m1pijl = models.BooleanField(default=False)
    discipline_outdoor = models.BooleanField(default=False)
    discipline_indoor = models.BooleanField(default=False)  # Indoor=18m/25m 3pijl, True als banen_18m>0 of banen_25m>0
    discipline_clout = models.BooleanField(default=False)
    discipline_veld = models.BooleanField(default=False)
    discipline_run = models.BooleanField(default=False)
    discipline_3d = models.BooleanField(default=False)
    # discipline_flight (zo ver mogelijk schieten)
    # discipline_ski

    # alleen voor indoor: beschikbare banen
    banen_18m = models.PositiveSmallIntegerField(default=0)
    banen_25m = models.PositiveSmallIntegerField(default=0)

    # het maximum aantal sporters
    # (noodzakelijk voor als max_sporters != banen * 4)
    max_sporters_18m = models.PositiveSmallIntegerField(default=0)
    max_sporters_25m = models.PositiveSmallIntegerField(default=0)

    # alleen voor discipline_outdoor baan
    buiten_banen = models.PositiveSmallIntegerField(default=0)
    buiten_max_afstand = models.PositiveSmallIntegerField(default=0)

    # adresgegevens van de locatie
    adres = models.TextField(max_length=256, blank=True)

    # plaats van deze locatie, om eenvoudig weer te kunnen geven op de kalender
    plaats = models.CharField(max_length=50, blank=True, default='')

    # handmatig ingevoerd of uit de CRM (=bevroren)
    adres_uit_crm = models.BooleanField(default=False)

    # vrije notitiegegevens voor zaken als "verbouwing tot", etc.
    notities = models.TextField(max_length=1024, blank=True)

    def disciplines_str(self):
        disc = list()
        if self.discipline_outdoor:
            disc.append('outdoor')
        if self.discipline_indoor:
            disc.append('indoor(18+25)')
        if self.discipline_25m1pijl:
            disc.append('25m1pijl')
        if self.discipline_clout:
            disc.append('clout')
        if self.discipline_veld:
            disc.append('veld')
        if self.discipline_run:
            disc.append('run')
        if self.discipline_3d:
            disc.append('3d')
        return ", ".join(disc)

    def __str__(self):
        if not self.zichtbaar:
            msg = "(hidden) "
        else:
            msg = ""

        msg += "[baantype: %s] " % BAANTYPE2STR[self.baan_type]

        msg += self.adres.replace('\n', ', ')
        # kost te veel database toegangen in admin interface
        # msg += " (%s verenigingen)" % self.verenigingen.count()

        msg += " [disciplines: %s]" % self.disciplines_str()

        msg += " [banen: 18m=%s, 25m=%s]" % (self.banen_18m, self.banen_25m)

        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Locatie"


# end of file
