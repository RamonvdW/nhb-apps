# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from django.utils import timezone
from Functie.definities import SCHEIDS_CHOICES, SCHEIDS_NIET
import datetime


# see https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#abstractuser
# on extending AbstractUser
class Account(AbstractUser):

    """ definitie van een account waarmee een gebruiker in kan loggen """

    # (replaced) username --> 150 to 50 chars
    username = models.CharField(
                    max_length=50,
                    unique=True,
                    help_text="Inlog naam")
    # (inherited) password
    # (inherited) date_joined
    # (inherited) last_login
    # (inherited) is_active  - may log in
    # (inherited) is_staff   - admin site access
    # (inherited) first_name
    # (inherited) last_name
    # (inherited) email            (not used)
    # (inherited) user_permissions (not used)
    # (inherited) is_superuser     (not used)
    # (inherited) groups           (not used)

    # om in te zoeken: volledige naam zonder leestekens
    unaccented_naam = models.CharField(max_length=200, default='', blank=True)

    vraag_nieuw_wachtwoord = models.BooleanField(
                                    default=False,
                                    help_text="Moet de gebruiker een nieuw wachtwoord opgeven bij volgende inlog?")

    laatste_inlog_poging = models.DateTimeField(blank=True, null=True)

    # verkeerd wachtwoord opgegeven via login of wijzig-wachtwoord
    verkeerd_wachtwoord_teller = models.IntegerField(
                                    default=0,
                                    help_text="Aantal mislukte inlog pogingen op rij")

    is_geblokkeerd_tot = models.DateTimeField(
                                    blank=True, null=True,
                                    help_text="Login niet mogelijk tot")

    # speciale vlag om dit account alle rechten te geven
    is_BB = models.BooleanField(
                        default=False,
                        help_text="Manager Competitiezaken")

    # TOTP ondersteuning
    otp_code = models.CharField(
                        max_length=32,          # 32-char base32 encoded secret
                        default="", blank=True,
                        help_text="OTP code")

    otp_is_actief = models.BooleanField(
                        default=False,
                        help_text="Is OTP verificatie gelukt")

    otp_controle_gelukt_op = models.DateTimeField(blank=True, null=True)

    # e-mail
    email_is_bevestigd = models.BooleanField(default=False)     # == mag inloggen
    bevestigde_email = models.EmailField(blank=True)
    nieuwe_email = models.EmailField(blank=True)

    # taken
    optout_nieuwe_taak = models.BooleanField(default=False)
    optout_herinnering_taken = models.BooleanField(default=False)
    laatste_email_over_taken = models.DateTimeField(blank=True, null=True)

    # is dit een gast-account (minder minder mogelijkheden)?
    is_gast = models.BooleanField(default=False)

    scheids = models.CharField(max_length=2, choices=SCHEIDS_CHOICES, default=SCHEIDS_NIET, blank=True)

    REQUIRED_FIELDS = ['password']

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def get_first_name(self):
        """ Deze functie wordt gebruikt om de voornaam van de gebruiker te krijgen
            voor in het menu.
            Vanuit template: user.get_first_name
        """
        return self.first_name or self.username

    def volledige_naam(self):
        """ Geef de volledige naam (voornaam achternaam) van het account terug
            als beide niet ingevuld zijn, geef dan de username terug
        """
        if self.first_name or self.last_name:
            name = self.first_name + " " + self.last_name
            return name.strip()

        return self.username

    def get_account_full_name(self):
        """ Deze functie wordt aangeroepen vanuit de site feedback om een volledige
            referentie aan de gebruiker te krijgen.

            Vanuit template: user.get_account_full_name
        """
        return "%s (%s)" % (self.volledige_naam(), self.username)

    def __str__(self):
        """ geef een korte beschrijving van dit account
            wordt gebruikt in de drop-down lijsten en autocomplete_fields van de admin interface
        """
        return self.get_account_full_name()


class AccountSessions(models.Model):
    """ Speciale table om bij te houden welke sessies bij een account horen
        zodat we deze eenvoudig kunnen benaderen.
    """

    # helaas gaat dit niet met een ManyToMany relatie, dus moet het zo
    # (based on https://gavinballard.com/associating-django-users-sessions/)

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)


class AccountVerzoekenTeller(models.Model):
    """ Deze tabel wordt gebruikt om voor elk account bij te houden hoe snel de verzoeken binnen komen.
        Als het te snel gaat, dan kunnen we een begrenzing stellen en daarmee misbruik voorkomen.

        We tellen een aantal verzoeken per uur. Als het uur nummer verandert, dan beginnen we weer op 0.
    """

    # bij welk account hoort deze administratie?
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # bij welk uur nummer hoort deze telling?
    uur_nummer = models.PositiveBigIntegerField(default=0)

    # aantal getelde verzoeken
    teller = models.PositiveIntegerField(default=0)


def accounts_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen nieuwe accounts die na 3 dagen nog niet voltooid zijn
    """

    now = timezone.now()
    wat_ouder = now - datetime.timedelta(days=3)

    # zoek gebruikers die een account aangemaakt hebben,
    # maar de mail niet binnen 3 dagen bevestigen
    # door deze te verwijderen kan de registratie opnieuw doorlopen worden
    for obj in (Account
                .objects
                .filter(email_is_bevestigd=False,
                        bevestigde_email='',
                        last_login=None,
                        date_joined__lt=wat_ouder)):

        stdout.write('[INFO] Verwijder onvoltooid account %s' % obj)
        obj.delete()
    # for


# end of file
