# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Locatie.models import WedstrijdLocatie
from Opleidingen.definities import OPLEIDING_STATUS_CHOICES, OPLEIDING_STATUS_VOORBEREID
from Sporter.models import Sporter
from decimal import Decimal


class OpleidingDiploma(models.Model):

    # welke sporter heeft deze opleiding behaald?
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # unieke code voor koppeling met CRM data
    # voorbeeld: 084 of 084a
    code = models.CharField(max_length=5, default='')

    # beschrijving van deze opleiding
    beschrijving = models.CharField(max_length=50, default='')

    # is deze om op de bondspas te tonen?
    # (voor queryset filter)
    toon_op_pas = models.BooleanField(default=False)

    # wanneer is de opleiding begonnen
    # 1990-01-01 = niet bekend, maar voor deze datum
    datum_begin = models.DateField(default='1990-01-01')

    # wanneer is de opleiding afgerond
    # 9999-12-31 = niet bekend
    datum_einde = models.DateField(default='9999-12-31')        # FUTURE: wordt niet gebruikt en kan weg?

    def __str__(self):
        return "%s: %s (%s)" % (self.sporter.lid_nr, self.code, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding diploma"

    objects = models.Manager()  # for the editor only


class OpleidingDeelnemer(models.Model):
    """ Deze klasse representeert een deelnemer aan een opleiding """

    sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT)

    # wanneer is deze aanmelding gedaan?
    wanneer_aangemeld = models.DateTimeField(auto_now_add=True)

    # wie was de koper?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # aanpassingen van de informatie die al/nog niet bekend is
    aanpassing_email = models.EmailField(blank=True)
    aanpassing_telefoon = models.CharField(max_length=25, default='', blank=True)
    aanpassing_geboorteplaats = models.CharField(max_length=100, default='', blank=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding deelnemer"

    objects = models.Manager()  # for the editor only


class OpleidingMoment(models.Model):
    """ details van een bijeenkomst van een opleiding """

    # wanneer is de bijeenkomst
    datum = models.DateField(default='2000-01-01')

    # hoe laat moeten de deelnemers aanwezig zijn
    begin_tijd = models.TimeField(default='10:00')

    # hoe lang duurt deze bijeenkomst
    duur_minuten = models.PositiveIntegerField(default=1)

    # waar moeten de deelnemers heen
    # TODO: wijzig naar EvenementLocatie
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT, blank=True, null=True)

    # naam en contactgegevens van de opleider
    opleider_naam = models.CharField(max_length=150, default='')
    opleider_email = models.EmailField(default='', blank=True)
    opleider_telefoon = models.CharField(max_length=25, default='', blank=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding moment"
        verbose_name_plural = "Opleiding momenten"

    objects = models.Manager()  # for the editor only


class Opleiding(models.Model):
    """ Deze klasse representeert een Opleiding """

    # een korte titel van de opleiding
    titel = models.CharField(max_length=75, default='')

    # periode waarin de opleiding gehouden gaat worden
    # kwartaal = 1/2/3/4
    periode_jaartal = models.PositiveSmallIntegerField(default=0)
    periode_kwartaal = models.PositiveIntegerField(default=1)

    # aantal bijeenkomsten (gepland)
    aantal_momenten = models.PositiveIntegerField(default=1)

    # leest van specifieke bijeenkomsten
    momenten = models.ManyToManyField(OpleidingMoment, blank=True)

    # aantal uren dat de opleiding vereist van de deelnemer
    aantal_uren = models.PositiveIntegerField(default=1)

    # uitgebreide beschrijving
    beschrijving = models.TextField(default='')

    # de status van deze opleiding
    status = models.CharField(max_length=1, choices=OPLEIDING_STATUS_CHOICES, default=OPLEIDING_STATUS_VOORBEREID)

    # beschrijving van de ingangseisen om mee te mogen doen
    ingangseisen = models.TextField()

    # begrenzing van de leeftijd voor deze opleiding
    # ondergrens met leeftijd_min, bovengrens met leeftijd_max
    # 0 = geen grens
    leeftijd_min = models.PositiveIntegerField(default=16)
    leeftijd_max = models.PositiveIntegerField(default=0)

    # de kosten voor de hele opleiding, in euros
    kosten_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))        # max 99999,99

    # lijst van de deelnemers
    deelnemers = models.ManyToManyField(OpleidingDeelnemer, blank=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding"
        verbose_name_plural = "Opleidingen"

    objects = models.Manager()  # for the editor only


# end of file
