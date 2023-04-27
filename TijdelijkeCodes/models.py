# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from datetime import timedelta
from Account.models import Account
from Competitie.models import KampioenschapSporterBoog
from Functie.models import Functie
from TijdelijkeCodes.operations import set_tijdelijke_code_saver
import datetime


class TijdelijkeCode(models.Model):
    """ Database tabel waarin de URLs staan die we naar buiten toe beschikbaar maken """

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
    hoortbij_account = models.ForeignKey(
                                Account,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optional

    hoortbij_functie = models.ForeignKey(
                                Functie,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optional

    hoortbij_kampioenschap = models.ForeignKey(
                                KampioenschapSporterBoog,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optioneel

    # in de toekomst meer mogelijkheden, zoals taken

    objects = models.Manager()      # for the editor only

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "(%s) bruikbaar tot %s; voor %s" % (self.pk, self.geldig_tot, self.dispatch_to)
        hoort_bij = list()
        if self.hoortbij_account:
            hoort_bij. append('account: %s' % self.hoortbij_account)
        if self.hoortbij_functie:
            hoort_bij.append('functie: %s' % self.hoortbij_functie)
        if self.hoortbij_kampioenschap:
            hoort_bij.append('kampioenschap: %s' % self.hoortbij_kampioenschap)
        msg += ' (%s)' % ", ".join(hoort_bij)
        return msg


def save_tijdelijke_code(url_code, dispatch_to, geldig_dagen=0, geldig_seconden=0, account=None, functie=None):

    if geldig_seconden > 0:
        delta = timedelta(seconds=geldig_seconden)
    else:
        delta = timedelta(days=geldig_dagen)

    now = timezone.now()

    # TODO: voorkom dubbele records voor dezelfde url_code
    # (voorbeeld: na elke inlog wordt code gebruikt voor bevestigen email)

    obj = TijdelijkeCode(
            url_code=url_code,
            aangemaakt_op=now,
            geldig_tot=now + delta,
            dispatch_to=dispatch_to,
            hoortbij_account=account,
            hoortbij_functie=functie)
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
