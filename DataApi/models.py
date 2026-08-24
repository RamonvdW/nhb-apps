# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


class DataApiVereniging(models.Model):
    """ representatie van een vereniging """

    # unieke nummer van deze vereniging
    # wordt gebruikt voor koppeling van lidmaatschappen met deze vereniging
    ver_nr = models.PositiveIntegerField()

    # naam van de vereniging
    naam = models.CharField(max_length=50)

    # datum van aanmelden en afmelden
    # formaat: YYYY-MM-DD
    aanmeld_datum = models.CharField(max_length=10)
    afmeld_datum = models.CharField(max_length=10, default='')      # leeg = niet afgemeld

    # KvK-nummer (optioneel)
    kvk_nummer = models.CharField(max_length=15, default='', blank=True)

    ### informatie over de "hoofdlocatie" ###

    # straatnaam van het bezoekadres van de locatie
    straatnaam = models.CharField(max_length=100)

    # huisnummer
    # ingeval van alfanumerieke tekens in het huisnummer: alleen het eerste numerieke deel
    huisnummer = models.PositiveIntegerField()

    # postcode
    postcode = models.CharField(max_length=6)

    # plaatsnaam
    plaats = models.CharField(max_length=50)

    # land code volgens ISO 3166-1
    # Altijd "NL" = Nederland
    land_iso = models.CharField(max_length=2, default="NL")

    # coördinaten voor het adres
    lat = models.CharField(max_length=10)       # 51.5037503
    lon = models.CharField(max_length=10)       # 5.3670660

    def __str__(self):
        msg = "[%s] %s (%s .. %s)" % (self.ver_nr, self.naam, self.aanmeld_datum, self.afmeld_datum)
        return msg

    class Meta:
        verbose_name = "DataApi Vereniging"
        verbose_name_plural = "DataApi Verenigingen"


class DataApiLidmaatschap(models.Model):
    """ representatie van een lidmaatschap """

    # uitgegeven nummer voor dit lid (kan hergebruikt worden)
    lid_nr = models.PositiveIntegerField()

    # geboortedatum van dit lid
    # formaat: YYYY-MM-DD
    geboorte_datum = models.CharField(max_length=10)

    # geslacht (m/v/x)
    geslacht = models.CharField(max_length=1)

    # land code volgens ISO 3166-1
    # "NL" = Nederland
    land_iso = models.CharField(max_length=2)

    # postcode
    # voor Nederlandse postcodes: "nnnnAA", zonder spaties
    # voor buitenlandse postcode: alles mag
    postcode = models.CharField(max_length=20)

    # datum van aanmelden en afmelden
    # formaat: YYYY-MM-DD
    aanmeld_datum = models.CharField(max_length=10)
    afmeld_datum = models.CharField(max_length=10, default='')      # leeg = niet afgemeld

    # lid bij welke vereniging? (verplicht)
    ver_nr = models.PositiveIntegerField()

    class Meta:
        verbose_name = "DataApi Lidmaatschap"
        verbose_name_plural = "DataApi Lidmaatschappen"


# end of file
