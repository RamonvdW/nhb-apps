# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Vereniging.definities import TYPE_EXTERNE_SCORES_ONBEKEND, TYPE_EXTERNE_SCORES_CHOICES
from Vereniging.models import Vereniging


class ExterneScores(models.Model):

    """ configuratie van een extern systeem waaruit scores te halen zijn
        voorlopig alleen voor de regiocompetitie
    """

    is_actief = models.BooleanField(default=False)

    # van welke vereniging
    vereniging = models.ForeignKey(Vereniging, on_delete=models.CASCADE)

    # type systeem
    type = models.PositiveSmallIntegerField(default=TYPE_EXTERNE_SCORES_ONBEKEND, choices=TYPE_EXTERNE_SCORES_CHOICES)

    # urls
    url_auth = models.CharField(max_length=128, blank=True, default='')
    url_ophalen = models.CharField(max_length=128, blank=True, default='')

    # authenticatie gegevens
    username = models.CharField(max_length=128, blank=True, default='')
    password = models.CharField(max_length=128, blank=True, default='')

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Externe scores"

    def __str__(self):
        msg = "[%s] " % self.vereniging.ver_nr
        if not self.is_actief:
            msg += ' (niet actief)'
        return msg


# end of file
