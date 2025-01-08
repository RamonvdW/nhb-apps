# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from datetime import timedelta
from Account.models import Account
from Competitie.models import KampioenschapSporterBoog
from Functie.models import Functie
from Sporter.models import Sporter
from Registreer.models import GastRegistratie
from TijdelijkeCodes.operations import set_tijdelijke_code_saver
from Wedstrijden.models import Wedstrijd
import datetime


class TijdelijkeCode(models.Model):
    """ Database tabel waarin de tijdelijke codes staan die we naar buiten toe beschikbaar maken """

    # de code die in de url gebruikt kan worden
    # om deze uniek te maken is het een hash over een aantal keywords die specifiek voor een gebruik zijn
    url_code = models.CharField(max_length=32)

    # wanneer aangemaakt door de website
    aangemaakt_op = models.DateTimeField()

    # tot wanneer mag deze tijdelijke code gebruikt worden?
    # verlopen codes kunnen niet meer gebruikt worden
    geldig_tot = models.DateTimeField()

    # zie do_dispatch in tijdelijke_url.py
    dispatch_to = models.CharField(max_length=20, default="")

    # extra velden voor de dispatcher
    hoort_bij_account = models.ForeignKey(
                                        Account,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)          # optional

    hoort_bij_gast_reg = models.ForeignKey(
                                        GastRegistratie,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)          # optional

    hoort_bij_functie = models.ForeignKey(
                                        Functie,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)          # optional

    hoort_bij_kampioen = models.ForeignKey(
                                        KampioenschapSporterBoog,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)          # optioneel

    # in de toekomst meer mogelijkheden, zoals taken

    objects = models.Manager()      # for the editor only

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "(%s) bruikbaar tot %s; voor %s" % (self.pk, self.geldig_tot, self.dispatch_to)
        hoort_bij = list()
        if self.hoort_bij_account:
            hoort_bij. append('account: %s' % self.hoort_bij_account)
        if self.hoort_bij_gast_reg:
            hoort_bij. append('gast registratie: %s' % self.hoort_bij_gast_reg)
        if self.hoort_bij_functie:
            hoort_bij.append('functie: %s' % self.hoort_bij_functie)
        if self.hoort_bij_kampioen:
            hoort_bij.append('kampioen: %s' % self.hoort_bij_kampioen)
        msg += ' (%s)' % ", ".join(hoort_bij)
        return msg


def save_tijdelijke_code(url_code, dispatch_to,
                         geldig_dagen=0, geldig_seconden=0,
                         account=None, gast=None, functie=None, kampioen=None, wedstrijd=None, sporter=None):

    if geldig_seconden > 0:
        delta = timedelta(seconds=geldig_seconden)
    else:
        delta = timedelta(days=geldig_dagen)

    now = timezone.now()

    # TODO: voorkom dubbele records voor dezelfde url_code
    # (voorbeeld: na elke inlog wordt code gebruikt voor bevestigen email)

    obj, is_created = TijdelijkeCode.objects.get_or_create(
                            url_code=url_code,
                            aangemaakt_op=now,
                            geldig_tot=now + delta,
                            dispatch_to=dispatch_to,
                            hoort_bij_account=account,
                            hoort_bij_gast_reg=gast,
                            hoort_bij_functie=functie,
                            hoort_bij_kampioen=kampioen)
    obj.save()

    return obj


set_tijdelijke_code_saver(save_tijdelijke_code)


def tijdelijke_url_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen tijdelijke urls die een week geleden verlopen zijn
        en afgehandelde site feedback van meer dan een kwartaal oud
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=7)

    for obj in (TijdelijkeCode
                .objects
                .filter(geldig_tot__lt=max_age)):

        stdout.write('[INFO] Verwijder ongebruikte tijdelijke url %s' % obj)
        obj.delete()
    # for

# end of file
