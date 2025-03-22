# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Locatie.definities import BAAN_TYPE_ONBEKEND, BAAN_TYPE, BAANTYPE2STR
from Vereniging.models import Vereniging


class WedstrijdLocatie(models.Model):
    """ Een locatie waarop een wedstrijd gehouden kan worden.

        Naast de accommodatie van de vereniging (binnen / buiten) ook externe locaties
        waar de vereniging een wedstrijd kan organiseren.
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

    # coördinaten voor het adres
    adres_lat = models.CharField(max_length=10, blank=True, default='')       # 51.5037503
    adres_lon = models.CharField(max_length=10, blank=True, default='')       # 5.3670660

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

    def adres_oneliner(self):
        # bij invoer via admin interface kan er een \r\n in de tekst komen
        return self.adres.replace('\r\n', '\n').replace('\n', ', ')

    def __str__(self):
        if not self.zichtbaar:
            msg = "(hidden) "
        else:
            msg = ""

        msg += "[baantype: %s] " % BAANTYPE2STR[self.baan_type]

        msg += self.adres_oneliner()
        # kost te veel database toegangen in admin interface
        # msg += " (%s verenigingen)" % self.verenigingen.count()

        msg += " [disciplines: %s]" % self.disciplines_str()

        msg += " [banen: 18m=%s, 25m=%s]" % (self.banen_18m, self.banen_25m)

        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijd locatie"


class EvenementLocatie(models.Model):
    """ Een locatie waarop een evenement of cursus gehouden kan worden.
    """

    # naam waaronder deze locatie getoond wordt
    naam = models.CharField(max_length=50, blank=True)

    # zichtbaar maakt het mogelijk een baan uit het systeem te halen
    # zonder deze helemaal te verwijderen
    zichtbaar = models.BooleanField(default=True)

    # vereniging die deze locatie aangemaakt heeft
    vereniging = models.ForeignKey(Vereniging, on_delete=models.CASCADE)

    # adresgegevens van de locatie
    adres = models.TextField(max_length=256, blank=True)

    # plaats van deze locatie, om eenvoudig weer te kunnen geven op de kalender
    plaats = models.CharField(max_length=50, blank=True, default='')

    # vrije notitiegegevens voor zaken als "verbouwing tot", etc.
    notities = models.TextField(max_length=1024, blank=True)

    def adres_oneliner(self):
        # bij invoer via admin interface kan er een \r\n in de tekst komen
        return self.adres.replace('\r\n', '\n').replace('\n', ', ')

    def __str__(self):
        # kost te veel database toegangen in admin interface?
        msg = "[%s] " % self.vereniging.ver_nr

        if not self.zichtbaar:
            msg += "(hidden) "

        msg += self.naam

        if self.plaats != self.naam:
            msg += ' ' + self.plaats

        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Evenement locatie"


class Reistijd(models.Model):

    """ Reistijd met de auto/motor, tussen twee postcodes.

        Coördination zijn nodig voor de API die we gebruiken.
        Deze komen uit OR voor zowel leden als het doel.
    """

    # coördinaten voor het vertrekpunt
    # note: 5e decimaal is ~1 meter
    vanaf_lat = models.CharField(max_length=10, default='')             # 51.5037503
    vanaf_lon = models.CharField(max_length=10, default='')             # 5.3670660

    # coördinaten voor het doel
    naar_lat = models.CharField(max_length=10, default='')
    naar_lon = models.CharField(max_length=10, default='')

    # reistijd enkele richting met auto/motor, in minuten
    # aankomsttijd 08:00 op een zaterdag of zondag
    reistijd_min = models.PositiveSmallIntegerField(default=0)   # max 32767

    # bijhouden hoe oud deze informatie is
    op_datum = models.DateField(default='2000-01-01')

    def __str__(self):
        return "%s minuten van %s, %s --> %s, %s" % (self.reistijd_min,
                                                     self.vanaf_lat, self.vanaf_lon,
                                                     self.naar_lat, self.naar_lon)

    def is_compleet(self):
        """ controleer dat alle input compleet is """
        if self.vanaf_lat == '' or self.vanaf_lon == '':
            return False
        if self.naar_lat == '' or self.naar_lon == '':
            return False
        return True

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Reistijd"
        verbose_name_plural = "Reistijden"


# end of file
