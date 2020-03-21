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
    url_code = models.CharField(max_length=32)
    aangemaakt_op = models.DateTimeField()
    geldig_tot = models.DateTimeField()
    hoortbij_accountemail = models.ForeignKey(AccountEmail,
                                              on_delete=models.CASCADE,
                                              blank=True, null=True)        # optional
    # in the toekomst meer mogelijkheden, zoals taken


def save_tijdelijke_url(url_code, geldig_dagen=0, accountemail=None):
    obj = SiteTijdelijkeUrl()
    obj.url_code = url_code
    obj.aangemaakt_op = timezone.now()
    obj.geldig_tot = obj.aangemaakt_op + timedelta(days=geldig_dagen)
    obj.hoortbij_accountemail = accountemail
    obj.save()


set_tijdelijke_url_saver(save_tijdelijke_url)

# end of file
