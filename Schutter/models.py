# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import models
from BasisTypen.models import BoogType
from Account.models import Account


class SchutterBoog(models.Model):
    """ Schutter met een specifiek type boog en zijn voorkeuren
        voor elk type boog waar de schutter interesse in heeft is er een entry
    """

    # het account waar dit record bij hoort
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)

    # voorkeuren van de schutter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    # voorkeur voor DT ipv 40cm blazoen (alleen voor 18m Recurve)
    voorkeur_dutchtarget_18m = models.BooleanField(default=False)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SchutterBoog"
        verbose_name_plural = "SchuttersBoog"

    def __str__(self):
        return "%s - %s" % (self.account.username, self.boogtype.beschrijving)
# end of file
