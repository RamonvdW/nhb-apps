# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
import datetime


class Feedback(models.Model):
    """ Database tabel waarin de feedback van de gebruikers staat """

    FEEDBACK = [('8', 'Tevreden'),
                ('6', 'Bruikbaar'),
                ('4', 'Moet beter')]

    # wanneer aangemaakt
    toegevoegd_op = models.DateTimeField(null=True)

    # welke versie van de website toen de feedback ingevoerd werd?
    site_versie = models.CharField(max_length=20)

    # wie heeft de feedback opgeschreven
    gebruiker = models.CharField(max_length=50)     # not linked to actual account

    # in welke rol is deze feedback gegeven
    in_rol = models.CharField(max_length=100, default='?', blank=True)

    # de naam van de pagina; typisch de naam van de template zoals "plein-beheerder"
    op_pagina = models.CharField(max_length=50)

    # volledige url naar deze pagina
    volledige_url = models.CharField(max_length=250, null=True, blank=True)

    # min/nul/plus
    bevinding = models.CharField(max_length=1, choices=FEEDBACK)

    # status
    is_afgehandeld = models.BooleanField(default=False)

    # vrije feedback van de gebruiker
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
        msg = "[%s] %s [%s] %s" % (timezone.localtime(self.toegevoegd_op).strftime('%Y-%m-%d %H:%M'),
                                   self.gebruiker,
                                   self.bev2str[self.bevinding],
                                   short_feedback)
        if self.is_afgehandeld:
            msg = "(afgehandeld) " + msg
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Feedback"

    objects = models.Manager()      # for the editor only


def feedback_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen afgehandelde feedback van meer dan een kwartaal oud
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=91)

    objs = (Feedback
            .objects
            .filter(is_afgehandeld=True,
                    toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s afgehandelde feedback' % count)
        objs.delete()


# end of file
