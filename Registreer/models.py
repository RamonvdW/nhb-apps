# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import GESLACHT_MVX, GESLACHT_MAN
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbVereniging
from Registreer.definities import REGISTRATIE_FASE_BEGIN
from Sporter.models import Sporter, validate_geboorte_datum


GAST_LID_NUMMER_FIXED_PK = 1


class GastLidNummer(models.Model):

    """ In deze tabel met maar 1 record met het vaste pk GAST_LID_NUMMER_FIXED_PK
        wordt bijgehouden wat het volgende te gebruiken lid nummer is voor gast-accounts
    """

    # het volgende vrije lidnummer wat toegekend kan worden
    volgende_lid_nr = models.PositiveIntegerField(primary_key=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = 'Volgende lid nr'


class GastRegistratie(models.Model):

    """ Tabel om details van een gast registratie bij te houden """

    # fases:
    # 1: toegang e-mailadres
    # 2: aanmaak account + sporter
    # 3: invoer alle benodigde gegevens

    # wanneer is deze registratie gestart?
    datum_aangemaakt = models.DateField(auto_now_add=True)

    # fase van het registratie-process
    fase = models.PositiveSmallIntegerField(default=REGISTRATIE_FASE_BEGIN)

    # voortgang bijhouden
    logboek = models.TextField(default='')

    # het unieke lidmaatschapsnummer
    lid_nr = models.PositiveIntegerField(default=0)

    # het e-mailadres waarop de gast bereikbaar is
    email_is_bevestigd = models.BooleanField(default=False)
    email = models.CharField(max_length=150)

    # koppeling met de standaard tabellen (null=True, want worden later aangemaakt)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE, null=True, blank=True)

    # aanmaken Sporter kan pas als alle informatie bekend is
    # alle ingevoerde informatie wordt hieronder opgeslagen voor traceability

    # volledige naam
    voornaam = models.CharField(max_length=50)
    tussenvoegsel = models.CharField(max_length=25)
    achternaam = models.CharField(max_length=100)

    # geboortedatum
    geboorte_datum = models.DateField(validators=[validate_geboorte_datum], default='2000-01-01')

    # geslacht (M/V/X)
    geslacht = models.CharField(max_length=1, choices=GESLACHT_MVX, default=GESLACHT_MAN)

    # naam van de sportbond in eigen land
    eigen_sportbond_naam = models.CharField(max_length=100, default='', blank=True)

    # lidmaatschapsnummer bij de eigen sportbond
    eigen_lid_nummer = models.CharField(max_length=25, default='', blank=True)

    # naam van vereniging in eigen land
    eigen_vereniging = models.CharField(max_length=100, default='', blank=True)

    # het adres van deze sporter
    woonplaats = models.CharField(max_length=100, default='', blank=True)
    land = models.CharField(max_length=100, default='', blank=True)

    # het telefoonnummer waarop de sporter te bereiken is
    telefoon = models.CharField(max_length=25, default='', blank=True)

    # TODO: officieel geregistreerde para classificatie
    # para_classificatie = models.CharField(max_length=30, blank=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Gast registratie'

    objects = models.Manager()      # for the editor only


class GastRegistratieRateTracker(models.Model):

    """ Om te voorkomen dat op hoge frequentie mails de deur uit gaan wordt het gebruik van deze
        functie bijgehouden voor elk specifiek IP adres.
    """

    # vanaf welk IP adres
    from_ip = models.CharField(max_length=48)

    # wanneer is er vanaf dit IP adres voor het laatst een verzoek gedaan
    vorige_gebruik = models.DateTimeField()

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Rate tracker'

    objects = models.Manager()      # for the editor only


# TODO: clean up old database record


# end of file
