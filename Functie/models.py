# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from Account.models import Account
from NhbStructuur.models import NhbRegio, NhbRayon, NhbVereniging
import enum

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


class Rollen(enum.IntEnum):
    """ definitie van de rollen met codes
        vertaling naar beschrijvingen in Plein.views
    """

    # rollen staan in prio volgorde
    ROL_BB = 2          # Manager Competitiezaken
    ROL_BKO = 3         # BK organisator, specifieke competitie
    ROL_RKO = 4         # RK organisator, specifieke competitie en rayon
    ROL_RCL = 5         # Regiocompetitieleider, specifieke competitie en regio
    ROL_HWL = 6         # Hoofdwedstrijdleider van een vereniging, alle competities
    ROL_WL = 7          # Wedstrijdleider van een vereniging, alle competities
    ROL_SEC = 10        # Secretaris van een vereniging
    ROL_SPORTER = 20    # Individuele sporter en NHB lid
    ROL_MWZ = 30        # Manager Wedstrijdzaken
    ROL_MO = 40         # Manager Opleidingen
    ROL_MWW = 50        # Manager Webwinkel
    ROL_SUP = 90        # Support
    ROL_NONE = 99       # geen rol (niet ingelogd)

    """ LET OP!
        rol nummers worden opgeslagen in de sessie
            verwijderen = probleem voor terugkerende gebruiker
            hergebruiken = gevaarlijk: gebruiker 'springt' naar nieuwe rol! 
        indien nodig alle sessies verwijderen
    """


url2rol = {
    'BB': Rollen.ROL_BB,
    'BKO': Rollen.ROL_BKO,
    'RKO': Rollen.ROL_RKO,
    'RCL': Rollen.ROL_RCL,
    'HWL': Rollen.ROL_HWL,
    'WL': Rollen.ROL_WL,
    'SEC': Rollen.ROL_SEC,
    'MO': Rollen.ROL_MO,
    'MWZ': Rollen.ROL_MWZ,
    'MWW': Rollen.ROL_MWW,
    'support': Rollen.ROL_SUP,
    'sporter': Rollen.ROL_SPORTER,
    'geen': Rollen.ROL_NONE
}

rol2url = {value: key for key, value in url2rol.items()}


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

    # BKO/RKO/RCL: voor de 18 (Indoor) of 25 (25m 1pijl) competitie?
    # leeg voor functies op verenigingsniveau (SEC, HWL, WL)
    comp_type = models.CharField(max_length=2, default="", blank=True)

    # RKO only: rayon
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT, null=True, blank=True)

    # RCL only: regio
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT, null=True, blank=True)

    # SEC/HWL/WL only: vereniging
    nhb_ver = models.ForeignKey(NhbVereniging, on_delete=models.CASCADE, null=True, blank=True)

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
