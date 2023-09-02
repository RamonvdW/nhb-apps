# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from BasisTypen.definities import GESLACHT_MVX, GESLACHT_MAN
from Registreer.definities import REGISTRATIE_FASE_BEGIN, REGISTRATIE_FASE2STR, REGISTRATIE_FASE_COMPLEET
from Sporter.models import Sporter, validate_geboorte_datum
import datetime

GAST_LID_NUMMER_FIXED_PK = 1


class GastLidNummer(models.Model):

    """ In deze tabel met maar 1 record met het vaste pk GAST_LID_NUMMER_FIXED_PK
        wordt bijgehouden wat het volgende te gebruiken lid nummer is voor gast-accounts
    """

    # het volgende vrije lidnummer wat toegekend kan worden
    volgende_lid_nr = models.PositiveIntegerField()

    # kill-switch voor registratie van nieuwe gast-accounts
    kan_aanmaken = models.BooleanField(default=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "Volgende = %s" % self.volgende_lid_nr

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = 'Volgende gast lid nr'


class GastRegistratie(models.Model):

    """ Tabel om details van een gast registratie bij te houden """

    # fases:
    # 1: toegang e-mailadres
    # 2: aanmaak account + sporter
    # 3: invoer alle benodigde gegevens

    # het unieke lidmaatschapsnummer
    lid_nr = models.PositiveIntegerField(default=0)

    # wanneer is deze registratie gestart?
    aangemaakt = models.DateTimeField(auto_now_add=True)

    # fase van het registratie-process
    fase = models.PositiveSmallIntegerField(default=REGISTRATIE_FASE_BEGIN)

    # het e-mailadres waarop de gast bereikbaar is
    email = models.CharField(max_length=150)
    email_is_bevestigd = models.BooleanField(default=False)

    # koppeling met de standaard tabellen (null=True, want worden later aangemaakt)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE, null=True, blank=True)

    # aanmaken Sporter kan pas als alle informatie bekend is
    # alle ingevoerde informatie wordt hieronder opgeslagen voor traceability

    # volledige naam
    voornaam = models.CharField(max_length=50)
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
    club = models.CharField(max_length=100, default='', blank=True)
    club_plaats = models.CharField(max_length=50, default='', blank=True)

    # het adres van deze sporter
    land = models.CharField(max_length=100, default='', blank=True)

    # het telefoonnummer waarop de sporter te bereiken is
    telefoon = models.CharField(max_length=25, default='', blank=True)

    # World Archery nummer van deze sporter
    wa_id = models.CharField(max_length=8, default='', blank=True)

    # TODO: officieel geregistreerde para classificatie
    # para_classificatie = models.CharField(max_length=30, blank=True)

    # voortgang bijhouden
    logboek = models.TextField(default='')

    def volledige_naam(self):
        return self.voornaam + " " + self.achternaam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Gast registratie'

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s [%s] %s: %s %s" % (self.aangemaakt.strftime('%Y-%m-%d %H:%M utc'),
                                      REGISTRATIE_FASE2STR[self.fase],
                                      self.lid_nr,
                                      self.voornaam, self.achternaam)

    objects = models.Manager()      # for the editor only


class GastRegistratieRateTracker(models.Model):

    """ Om te voorkomen dat op hoge frequentie mails de deur uit gaan wordt het gebruik van deze
        functie bijgehouden voor elk specifiek IP adres.
    """

    # vanaf welk IP adres
    from_ip = models.CharField(max_length=48)

    # aantal minuten sinds middernacht
    minuut = models.PositiveSmallIntegerField(default=0)

    # aantal verzoeken in deze minuut
    teller_minuut = models.PositiveSmallIntegerField(default=0)

    # aantal verzoeken binnen dit uur
    uur = models.PositiveSmallIntegerField(default=0)
    teller_uur = models.PositiveSmallIntegerField(default=0)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Rate tracker'

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s: %s" % (self.from_ip, self.teller_uur)

    objects = models.Manager()      # for the editor only


def registreer_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen gast registratie die na 7 dagen nog niet voltooid zijn
        We verwijderen rate tracker records die niet meer nodig zijn
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=7)

    for obj in (GastRegistratie
                .objects
                .filter(fase__lte=REGISTRATIE_FASE_COMPLEET,        # skip COMPLEET of AFGEWEZEN
                        aangemaakt__lt=max_age)):

        stdout.write('[INFO] Verwijder niet afgeronde gast-account registratie %s in fase %s' % (
                        obj.lid_nr, repr(obj.fase)))

        # TODO: activeer opschonen nadat wat ervaring opgedaan is
        if GAST_LID_NUMMER_FIXED_PK < 1:  # aka: "never"
            obj.delete()
    # for

    # alle rate trackers opruimen
    GastRegistratieRateTracker.objects.all().delete()


# end of file
