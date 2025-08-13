# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from uuid import uuid5, NAMESPACE_URL
from Sporter.models import Sporter

uuid_namespace = uuid5(NAMESPACE_URL, 'GoogleDrive.Models.Transactie')


class Transactie(models.Model):
    """ Deze tabel houdt de (asynchrone) interacties met Google bij.
        Dit gebruiken om webhook aanroepen te filteren.
    """

    # datum/tijdstip van aanmaak (wordt gebruikt voor opschonen)
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # de Google API geeft ons de mogelijk om een "state" door te geven
    # we gebruiken dit voor een unieke code en gebruiken dit om de webhook te beveiligen tegen misbruik
    unieke_code = models.CharField(max_length=32)

    # elke transactie is maar 1x bruikbaar
    has_been_used = models.BooleanField(default=False)

    # logboek met status veranderingen
    log = models.TextField(default='')

    class Meta:
        verbose_name = "Transactie"

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "[%s]" % timezone.localtime(self.when).strftime('%Y-%m-%d %H:%M:%S')
        msg += " %s" % self.unieke_code
        return msg


class Token(models.Model):
    """ Deze tabel slaat de tokens op die we hebben gekregen van Google """

    # datum/tijdstip van aanmaak (wordt gebruikt voor opschonen)
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # token ontvangen in de authorization response
    creds = models.JSONField(default=dict)

    # logboek met status veranderingen
    log = models.TextField(default='')

    class Meta:
        verbose_name = "Token"

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "[%s]" % timezone.localtime(self.when).strftime('%Y-%m-%d %H:%M:%S')
        return msg


class Bestand(models.Model):
    """ Deze tabel houdt bij:
        - welke bestanden aangemaakt hebben
        - wat het file_id is in de Google Drive
        - met wie we het bestand gedeeld hebben
    """

    # drie parameters die de folder bepalen
    afstand = models.PositiveSmallIntegerField(default=0)       # 18 (Indoor) of 25 (25m1pijl)
    is_team = models.BooleanField(default=False)                # team of individueel
    is_bk = models.BooleanField(default=False)                  # RK of BK

    # naam van het bestand is afhankelijk van de wedstrijdklasse
    fname = models.CharField(max_length=80)

    # file_id returned by the Google Drive API
    file_id = models.CharField(max_length=64, default='')       # 32 should be enough

    # met welke beheerders is dit bestand gedeeld?
    sporters = models.ManyToManyField(Sporter)

    # logboekje van acties op deze file: aanmaken, delen met HWL, bijgewerkt, problemen, etc.
    log = models.TextField(default='')

    class Meta:
        verbose_name = "Bestand"
        verbose_name_plural = "Bestanden"


def maak_unieke_code(**kwargs):
    """ Bereken een unieke code die we kunnen gebruiken in een URL
    """
    return uuid5(uuid_namespace, repr(kwargs)).hex


# end of file
