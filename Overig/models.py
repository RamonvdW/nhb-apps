# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from Account.models import AccountEmail
from .tijdelijke_url import set_tijdelijke_url_saver


class SiteFeedback(models.Model):
    """ Database tabel waarin de feedback van de gebruikers staat """

    FEEDBACK = [('8', 'Tevreden'),
                ('6', 'Bruikbaar'),
                ('4', 'Moet beter')]

    toegevoegd_op = models.DateTimeField()
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
        msg = "[%s] %s (%s) pagina '%s': [%s] %s" % (self.site_versie,
                                        self.toegevoegd_op.strftime('%Y-%m-%d %H:%M utc'),
                                        self.gebruiker,
                                        self.op_pagina,
                                        self.bev2str[self.bevinding],
                                        short_feedback)
        if self.is_afgehandeld:
            msg = "(afgehandeld) " + msg
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Site feedback"

    objects = models.Manager()      # for the editor only


def store_feedback(gebruiker, op_pagina, bevinding, feedback):
    """ Deze functie wordt aangeroepen vanuit de view waarin de feedback van de gebruiker
        verzameld is. Deze functie slaat de feedback op in een database tabel.
    """
    obj = SiteFeedback()
    obj.toegevoegd_op = timezone.now()
    obj.site_versie = settings.SITE_VERSIE
    obj.gebruiker = gebruiker
    obj.op_pagina = op_pagina
    obj.bevinding = bevinding
    obj.feedback = feedback
    obj.is_afgehandeld = False
    obj.save()


# class SiteControl(models.Model):
#    onderhoud_start = models.DateTimeField()
#    onderhoud_klaar = models.DateTimeField()
#    onderhoud_bericht = models.TextField()


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
    hoortbij_accountemail = models.ForeignKey(AccountEmail,
                                              on_delete=models.CASCADE,
                                              blank=True, null=True)        # optional
    # in de toekomst meer mogelijkheden, zoals taken

    objects = models.Manager()      # for the editor only


def save_tijdelijke_url(url_code, dispatch_to, geldig_dagen=0, geldig_seconden=0, accountemail=None):
    obj = SiteTijdelijkeUrl()
    obj.url_code = url_code
    obj.aangemaakt_op = timezone.now()
    if geldig_seconden > 0:
        obj.geldig_tot = obj.aangemaakt_op + timedelta(seconds=geldig_seconden)
    else:
        obj.geldig_tot = obj.aangemaakt_op + timedelta(days=geldig_dagen)
    obj.dispatch_to = dispatch_to
    obj.hoortbij_accountemail = accountemail
    obj.save()


set_tijdelijke_url_saver(save_tijdelijke_url)

# end of file
