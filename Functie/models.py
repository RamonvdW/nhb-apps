# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from Account.models import Account
from Geo.models import Regio, Rayon
from Vereniging.models import Vereniging


""" Deze module houdt bij wie beheerders zijn

    Functies: BKO, RKO, RCL, HWL, etc. zijn functies
    (BB: staat in het Account als is_BB)
    (IT: staat in het Account als is_staff - alleen voor toegang Admin)
    
    Een Account is lid van een of meerdere functies
        Hiermee wordt het Account gekoppeld aan een Functie
        en krijgt de gebruiker 'rechten'
        
    Voorbeeld:
        Account = '123456'
        Account.functies = [Functie: 'RKO Rayon 1']
"""

"""
    Standaard functies zijn aangemaakt door de migratie functies van deze app
    BKO Indoor
    RKO Rayon 1 Indoor
    RKO Rayon 2 Indoor
    etc.
    RCL Regio 101 Indoor
    RCL Regio 102 Indoor
    etc.
    BKO 25m 1pijl
    etc.
"""


class Functie(models.Model):

    """ Deze klasse representeert een Functie met rechten """

    # welke accounts zijn gekoppeld aan deze functie
    accounts = models.ManyToManyField(Account,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # in principe vrije tekst
    beschrijving = models.CharField(max_length=50)

    # een aantal velden om de juiste Functie te kunnen koppelen

    # BKO, RKO, etc. (zie rol.py)
    rol = models.CharField(max_length=5)

    # email adres wat bij deze functie hoort
    bevestigde_email = models.EmailField(blank=True)
    nieuwe_email = models.EmailField(blank=True)

    # taken
    optout_nieuwe_taak = models.BooleanField(default=False)
    optout_herinnering_taken = models.BooleanField(default=False)
    laatste_email_over_taken = models.DateTimeField(blank=True, null=True)

    # telefoonnummer wat bij deze functie hoort (optioneel)
    telefoon = models.CharField(max_length=25, default='', blank=True)

    # BKO/RKO/RCL: voor de "18" (Indoor) of "25" (25m 1pijl) competitie
    # leeg voor functies op verenigingsniveau (SEC, HWL, WL)
    comp_type = models.CharField(max_length=2, default="", blank=True)

    # RKO only: rayon
    rayon = models.ForeignKey(Rayon, on_delete=models.PROTECT, null=True, blank=True)

    # RCL only: regio
    regio = models.ForeignKey(Regio, on_delete=models.PROTECT, null=True, blank=True)

    # SEC/HWL/WL/LA only: vereniging
    vereniging = models.ForeignKey(Vereniging, on_delete=models.CASCADE, null=True, blank=True)

    def is_indoor(self):
        return self.comp_type == '18'

    def is_25m1pijl(self):
        return self.comp_type == '25'

    def kort(self):
        msg = self.rol
        if self.rayon:
            msg += str(self.rayon_id)       # gelijk aan rayon_nr
        elif self.regio:
            msg += str(self.regio_id)       # gelijk aan regio_nr
        elif self.vereniging:
            msg += " " + str(self.vereniging.ver_nr)
        return msg

    def __str__(self):
        """ Geef een string terug voor gebruik in de admin interface """
        return self.beschrijving

    objects = models.Manager()      # for the editor only


class VerklaringHanterenPersoonsgegevens(models.Model):
    """ status van de vraag om juist om te gaan met persoonsgegevens,
        voor de paar accounts waarvoor dit relevant is.
    """

    # het account waar dit record bij hoort
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='vhpg')

    # datum waarop de acceptatie voor het laatste gedaan is
    acceptatie_datum = models.DateTimeField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        to_tz = timezone.get_default_timezone()
        return "[%s] %s" % (self.account.username, date_format(self.acceptatie_datum.astimezone(to_tz), 'j F Y H:i'))

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Verklaring Hanteren Persoonsgegevens"
        verbose_name_plural = "Verklaring Hanteren Persoonsgegevens"

    objects = models.Manager()      # for the editor only


# end of file
