# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils.formats import localize
from Account.models import Account
from Locatie.models import EvenementLocatie
from Opleiding.definities import (OPLEIDING_STATUS_CHOICES, OPLEIDING_STATUS_VOORBEREID,
                                  OPLEIDING_INSCHRIJVING_STATUS_CHOICES,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_AFMELDING_STATUS_CHOICES, OPLEIDING_AFMELDING_STATUS_TO_STR)
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


class OpleidingMoment(models.Model):
    """ details van een bijeenkomst van een opleiding """

    # wanneer is de bijeenkomst
    datum = models.DateField(default='2000-01-01')

    # hoe laat moeten de deelnemers aanwezig zijn
    begin_tijd = models.TimeField(default='10:00')

    # hoe lang duurt deze bijeenkomst
    duur_minuten = models.PositiveIntegerField(default=1)

    # waar moeten de deelnemers heen
    locatie = models.ForeignKey(EvenementLocatie, on_delete=models.PROTECT, blank=True, null=True)

    # naam en contactgegevens van de opleider
    opleider_naam = models.CharField(max_length=150, default='')
    opleider_email = models.EmailField(default='', blank=True)
    opleider_telefoon = models.CharField(max_length=25, default='', blank=True)

    def __str__(self):
        msg = "%s %s (%s min)" % (self.datum, str(self.begin_tijd)[:5], self.duur_minuten)
        if self.locatie:
            msg += " [%s]" % self.locatie.plaats
        msg += " " + self.opleider_naam
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding moment"
        verbose_name_plural = "Opleiding momenten"

    objects = models.Manager()  # for the editor only


class Opleiding(models.Model):
    """ Deze klasse representeert een Opleiding """

    # een korte titel van de opleiding
    titel = models.CharField(max_length=75, default='')

    # deze nog tonen op de lijst met opleidingen?
    laten_zien = models.BooleanField(default=True)

    # is dit een basiscursus?
    is_basiscursus = models.BooleanField(default=False)

    # periode waarin de opleiding gehouden gaat worden
    # kwartaal = 1/2/3/4
    periode_begin = models.DateField(default='2024-01-01')
    periode_einde = models.DateField(default='2024-01-01')

    # aantal bijeenkomsten (gepland)
    aantal_momenten = models.PositiveIntegerField(default=1)

    # lijst van specifieke bijeenkomsten
    momenten = models.ManyToManyField(OpleidingMoment, blank=True)

    # duur van de opleiding in dagen
    aantal_dagen = models.PositiveSmallIntegerField(default=1)

    # aantal uren dat de opleiding vereist van de deelnemer
    aantal_uren = models.PositiveSmallIntegerField(default=1)

    # uitgebreide beschrijving
    beschrijving = models.TextField(default='', blank=True)

    # de status van deze opleiding
    status = models.CharField(max_length=1, choices=OPLEIDING_STATUS_CHOICES, default=OPLEIDING_STATUS_VOORBEREID)

    # is de instaptoets een vereiste?
    eis_instaptoets = models.BooleanField(default=False, blank=True)

    # beschrijving van de ingangseisen om mee te mogen doen
    ingangseisen = models.TextField(default='', blank=True)

    # begrenzing van de leeftijd voor deze opleiding
    # ondergrens met leeftijd_min, bovengrens met leeftijd_max
    # 0 = geen grens
    leeftijd_min = models.PositiveIntegerField(default=16)
    leeftijd_max = models.PositiveIntegerField(default=0)

    # de kosten voor de hele opleiding, in euros
    kosten_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))        # max 99999,99

    def periode_str(self):
        # localize() geeft "1 januari 2024"
        wanneer_str = localize(self.periode_begin)
        # verwijder de dag
        wanneer_str = wanneer_str.replace(str(self.periode_begin.day), '').strip()

        if self.periode_begin != self.periode_einde:
            # localize() geeft "1 januari 2024"
            einde_str = localize(self.periode_einde)
            # verwijder de dag
            einde_str = einde_str.replace(str(self.periode_einde.day), '').strip()

            if self.periode_begin.year == self.periode_einde.year:
                # verwijder het jaartal
                wanneer_str = wanneer_str.replace(str(self.periode_begin.year), '').strip()

            wanneer_str += " tot " + einde_str

        return wanneer_str

    def __str__(self):
        return "%s [%s]" % (self.titel, self.periode_str())

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding"
        verbose_name_plural = "Opleidingen"

    objects = models.Manager()  # for the editor only


class OpleidingInschrijving(models.Model):
    """ Deze klasse representeert een inschrijving voor een opleiding """

    # welke opleiding gaat dit om?
    opleiding = models.ForeignKey(Opleiding, on_delete=models.PROTECT)

    # wie is de deelnemer?
    sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT)

    # wanneer is deze aanmelding gedaan?
    wanneer_aangemeld = models.DateTimeField(auto_now_add=True)

    # het reserveringsnummer
    nummer = models.BigIntegerField(default=0)

    # status
    status = models.CharField(max_length=2, choices=OPLEIDING_INSCHRIJVING_STATUS_CHOICES,
                              default=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

    # wie was de koper?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True)

    # bedragen ontvangen en terugbetaald
    bedrag_ontvangen = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # aanpassingen van de informatie die al/nog niet bekend is
    aanpassing_email = models.EmailField(blank=True)
    aanpassing_telefoon = models.CharField(max_length=25, default='', blank=True)
    aanpassing_geboorteplaats = models.CharField(max_length=100, default='', blank=True)

    # log van bestelling, betalingen en eventuele wijzigingen
    log = models.TextField(blank=True)

    def korte_beschrijving(self):
        return self.opleiding.titel

    def __str__(self):
        return "[%s] %s %s" % (self.pk, self.sporter.lid_nr_en_volledige_naam(), self.opleiding)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Opleiding inschrijving"
        verbose_name_plural = "Opleiding inschrijvingen"

    objects = models.Manager()  # for the editor only


class OpleidingAfgemeld(models.Model):
    """ Deze klasse representeert een deelnemer die afgemeld is voor een opleiding """

    # wanneer is deze afmelding gedaan?
    wanneer_afgemeld = models.DateTimeField(auto_now_add=True)

    # status van deze afmelding
    status = models.CharField(max_length=2, choices=OPLEIDING_AFMELDING_STATUS_CHOICES)

    # welke opleiding ging het?
    opleiding = models.ForeignKey(Opleiding, on_delete=models.PROTECT)

    # wie was de deelnemer?
    sporter = models.ForeignKey(Sporter, on_delete=models.PROTECT)

    # wanneer was de aanmelding gedaan?
    wanneer_aangemeld = models.DateTimeField(auto_now_add=True)

    # het originele reserveringsnummer
    nummer = models.BigIntegerField(default=0)

    # wie was de koper?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True)

    # bedragen ontvangen en terugbetaald
    bedrag_ontvangen = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    bedrag_retour = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # aanpassingen van de informatie die al/nog niet bekend is
    aanpassing_email = models.EmailField(blank=True)
    aanpassing_telefoon = models.CharField(max_length=25, default='', blank=True)
    aanpassing_geboorteplaats = models.CharField(max_length=100, default='', blank=True)

    # log van bestelling, betalingen en eventuele wijzigingen
    log = models.TextField(blank=True)

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Afmelding voor %s: [%s]" % (self.sporter.lid_nr_en_volledige_naam(),
                                            OPLEIDING_AFMELDING_STATUS_TO_STR[self.status])

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze afmelding """
        return self.opleiding.titel

    class Meta:
        verbose_name = "Opleiding afmelding"
        verbose_name_plural = "Opleiding afmeldingen"

    objects = models.Manager()      # for the editor only

# end of file
