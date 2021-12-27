# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from datetime import timedelta
from Account.models import AccountEmail
from Competitie.models import KampioenschapSchutterBoog
from Functie.models import Functie
from .tijdelijke_url import set_tijdelijke_url_saver
import datetime


class SiteFeedback(models.Model):
    """ Database tabel waarin de feedback van de gebruikers staat """

    FEEDBACK = [('8', 'Tevreden'),
                ('6', 'Bruikbaar'),
                ('4', 'Moet beter')]

    toegevoegd_op = models.DateTimeField(null=True)
    site_versie = models.CharField(max_length=20)
    gebruiker = models.CharField(max_length=50)     # not linked to actual account
    op_pagina = models.CharField(max_length=50)
    bevinding = models.CharField(max_length=1, choices=FEEDBACK)
    is_afgehandeld = models.BooleanField(default=False)
    feedback = models.TextField()

    url2bev = {
        'plus': '8',
        'nul': '6',
        'min': '4'
    }

    bev2str = {
        '8': 'Tevreden',
        '6': 'Bruikbaar',
        '4': 'Moet beter'
    }

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        short_feedback = self.feedback[:60]
        if len(self.feedback) > 60:
            short_feedback += "..."
        msg = "[%s] %s [%s] %s" % (self.toegevoegd_op.strftime('%Y-%m-%d %H:%M utc'),
                                   self.gebruiker,
                                   self.bev2str[self.bevinding],
                                   short_feedback)
        if self.is_afgehandeld:
            msg = "(afgehandeld) " + msg
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Site feedback"

    objects = models.Manager()      # for the editor only


class SiteTijdelijkeUrl(models.Model):
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
    hoortbij_accountemail = models.ForeignKey(
                                AccountEmail,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optional

    hoortbij_functie = models.ForeignKey(
                                Functie,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optional

    hoortbij_kampioenschap = models.ForeignKey(
                                KampioenschapSchutterBoog,
                                on_delete=models.CASCADE,
                                blank=True, null=True)        # optioneel

    # in de toekomst meer mogelijkheden, zoals taken

    objects = models.Manager()      # for the editor only

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "(%s) bruikbaar tot %s; voor %s" % (self.pk, self.geldig_tot, self.dispatch_to)
        hoort_bij = list()
        if self.hoortbij_accountemail:
            hoort_bij. append('accountemail: %s' % self.hoortbij_accountemail)
        if self.hoortbij_functie:
            hoort_bij.append('functie: %s' % self.hoortbij_functie)
        if self.hoortbij_kampioenschap:
            hoort_bij.append('kampioenschap: %s' % self.hoortbij_kampioenschap)
        msg += ' (%s)' % ", ".join(hoort_bij)
        return msg


def save_tijdelijke_url(url_code, dispatch_to, geldig_dagen=0, geldig_seconden=0, accountemail=None, functie=None):
    obj = SiteTijdelijkeUrl()
    obj.url_code = url_code
    obj.aangemaakt_op = timezone.now()
    if geldig_seconden > 0:
        obj.geldig_tot = obj.aangemaakt_op + timedelta(seconds=geldig_seconden)
    else:
        obj.geldig_tot = obj.aangemaakt_op + timedelta(days=geldig_dagen)
    obj.dispatch_to = dispatch_to
    obj.hoortbij_accountemail = accountemail
    obj.hoortbij_functie = functie
    obj.save()
    return obj


set_tijdelijke_url_saver(save_tijdelijke_url)


def overig_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen tijdelijke urls die een week geleden verlopen zijn
        en afgehandelde site feedback van meer dan een kwartaal oud
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=7)

    for obj in (SiteTijdelijkeUrl
                .objects
                .filter(geldig_tot__lt=max_age)):

        stdout.write('[INFO] Verwijder ongebruikte tijdelijke url %s' % obj)
        obj.delete()
    # for

    max_age = now - datetime.timedelta(days=91)

    objs = (SiteFeedback
            .objects
            .filter(is_afgehandeld=True,
                    toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s afgehandelde site feedback' % count)
        objs.delete()


# end of file
