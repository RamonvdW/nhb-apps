# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account


class LogboekRegel(models.Model):
    """ definitie van een regel in het logboek """
    toegevoegd_op = models.DateTimeField()
    actie_door_account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                           blank=True,  # allow access input in form
                                           null=True)  # allow NULL relation in database
    gebruikte_functie = models.CharField(max_length=100)
    activiteit = models.CharField(max_length=500)

    def bepaal_door(self):
        """ bepaal door wie actie uitgevoerd is """
        if not self.actie_door_account:
            return 'Systeem of IT beheerder'
        return self.actie_door_account.username

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s (%s) %s" % (self.toegevoegd_op.strftime('%Y-%m-%d %H:%M'),
                               self.bepaal_door(),
                               self.gebruikte_functie)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Logboek regel"
        verbose_name_plural = "Logboek regels"


def schrijf_in_logboek(account, gebruikte_functie, activiteit):
    """ Deze functie wordt aangeroepen vanuit de view waarin de feedback van de gebruiker
        verzameld is. Deze functie slaat de feedback op in een database tabel.
    """
    obj = LogboekRegel()
    obj.toegevoegd_op = timezone.now()
    obj.actie_door_account = account
    obj.gebruikte_functie = gebruikte_functie
    obj.activiteit = activiteit
    obj.save()


# end of file
