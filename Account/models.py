# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from Overig.tijdelijke_url import maak_tijdelijke_url_account_email
from Mailer.models import mailer_email_is_valide
from django.utils import timezone
import datetime


class AccountCreateError(Exception):
    """ Generic exception raised by account_create """
    pass


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
    # (inherited) is_active     - may log in
    # (inherited) is_staff      - admin site access
    # (inherited) is_superuser  - all permissions
    # (inherited) first_name
    # (inherited) last_name
    # (inherited, not used) email
    # (inherited) user_permissions: ManyToMany
    # (inherited) groups: ManyToMany

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

    # rollen / functies
    is_BB = models.BooleanField(
                        default=False,
                        help_text="Manager Competitiezaken")

    is_Observer = models.BooleanField(
                        default=False,
                        help_text="Alleen observeren")

    # TOTP ondersteuning
    otp_code = models.CharField(
                        max_length=32,          # 32-char base32 encoded secret
                        default="", blank=True,
                        help_text="OTP code")

    otp_is_actief = models.BooleanField(
                        default=False,
                        help_text="Is OTP verificatie gelukt")

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

            Wordt ook gebruikt vanuit djangosaml2idp
            in settings.py staat de referentie naar deze methode naam
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

    def get_email(self):
        """ helper om de email van de gebruiker te krijgen voor djangosaml2idp
            zodat deze doorgegeven kan worden aan een Service Provider zoals de Wiki server
            in settings.py staat de referentie naar deze methode naam
        """
        if self.accountemail_set.count() == 1:
            email = self.accountemail_set.all()[0].bevestigde_email
        else:
            email = ""
        return email

    def __str__(self):
        """ geef een korte beschrijving van dit account
            wordt gebruikt in de drop-down lijsten en autocomplete_fields van de admin interface
        """
        return self.get_account_full_name()


class AccountEmail(models.Model):
    """ definitie van een e-mail adres (en de status daarvan) voor een account """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # e-mail
    email_is_bevestigd = models.BooleanField(default=False)     # == mag inloggen
    bevestigde_email = models.EmailField(blank=True)
    nieuwe_email = models.EmailField(blank=True)

    # taken
    optout_nieuwe_taak = models.BooleanField(default=False)
    optout_herinnering_taken = models.BooleanField(default=False)
    laatste_email_over_taken = models.DateTimeField(blank=True, null=True)

    # functie koppeling
    optout_functie_koppeling = models.BooleanField(default=False)

    # klachten
    optout_reactie_klacht = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "E-mail voor account '%s' (%s)" % (self.account.username,
                                                  self.bevestigde_email)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "AccountEmail"
        verbose_name_plural = "AccountEmails"

    objects = models.Manager()      # for the editor only


def account_create(username, voornaam, achternaam, wachtwoord, email, email_is_bevestigd):
    """ Maak een nieuw Account aan met een willekeurige naam
        Email wordt er meteen in gezet en heeft geen bevestiging nodig
    """

    if not mailer_email_is_valide(email):
        raise AccountCreateError('Dat is geen valide e-mail')

    if Account.objects.filter(username=username).count() != 0:
        raise AccountCreateError('Account bestaat al')

    # maak het account aan
    account = Account()
    account.username = username
    account.set_password(wachtwoord)
    account.first_name = voornaam
    account.last_name = achternaam
    account.save()

    # maak het email record aan
    mail = AccountEmail()
    mail.account = account
    if email_is_bevestigd:
        mail.email_is_bevestigd = True
        mail.bevestigde_email = email
        mail.nieuwe_email = ''
    else:
        mail.email_is_bevestigd = False
        mail.bevestigde_email = ''
        mail.nieuwe_email = email
    mail.save()

    return account, mail


def account_email_bevestiging_ontvangen(mail):
    """ Deze functie wordt vanuit de tijdelijke url receiver functie (zie view)
        aanroepen met mail = AccountEmail object waar dit op van toepassing is
    """
    # voorkom verlies van een bevestigde email bij interne fouten
    if mail.nieuwe_email != '':
        mail.bevestigde_email = mail.nieuwe_email
        mail.nieuwe_email = ''
        mail.email_is_bevestigd = True
        mail.save()


def account_check_gewijzigde_email(account):
    """ Zoek uit of dit account een nieuw email adres heeft wat nog bevestigd
        moet worden. Zoja, dan wordt ereen tijdelijke URL aangemaakt en het emailadres terug gegeven
        waar een mailtje heen gestuurd moet worden.

        Retourneert: tijdelijke_url, nieuwe_mail_adres
                 of: None, None
    """

    if account.accountemail_set.count() > 0:
        email = account.accountemail_set.all()[0]

        if email.nieuwe_email:
            if email.nieuwe_email != email.bevestigde_email:
                # vraag om bevestiging van deze gewijzgde email
                # email kan eerder overgenomen zijn uit de NHB administratie
                # of handmatig ingevoerd zijn

                # blokkeer inlog totdat dit nieuwe emailadres bevestigd is
                email.email_is_bevestigd = False
                email.save()

                # maak de url aan om het emailadres te bevestigen
                # extra parameters are just to make the url unique
                mailadres = email.nieuwe_email
                url = maak_tijdelijke_url_account_email(email, username=account.username, email=mailadres)
                return url, mailadres

    # geen gewijzigde email
    return None, None


# alles in kleine letter
VERBODEN_WOORDEN_IN_WACHTWOORD = (
    'password',
    'wachtwoord',
    'geheim',
    'handboog',
    # keyboard walks
    '12345',
    '23456',
    '34567',
    '45678',
    '56789',
    '67890',
    'qwert',
    'werty',
    'ertyu',
    'rtyui',
    'tyuio',
    'yuiop',
    'asdfg',
    'sdfgh',
    'dfghj',
    'fghjk',
    'ghjkl',
    'zxcvb',
    'xcvbn',
    'cvbnm'
)


def account_test_wachtwoord_sterkte(wachtwoord, verboden_str):
    """ Controleer de sterkte van het opgegeven wachtwoord
        Retourneert: True,  None                als het wachtwoord goed genoeg is
                     False, "een error message" als het wachtwoord niet goed genoeg is
    """

    # we willen voorkomen dat mensen eenvoudig te RADEN wachtwoorden kiezen
    # of wachtwoorden die eenvoudig AF TE KIJKEN zijn

    # controleer de minimale length
    if len(wachtwoord) < 9:
        return False, "Wachtwoord moet minimaal 9 tekens lang zijn"

    # verboden_str is de inlog naam
    if verboden_str in wachtwoord:
        return False, "Wachtwoord bevat een verboden reeks"

    # entropie van elk teken is gelijk, dus het verminderen van de zoekruimte is niet verstandig
    # dus NIET: controleer op alleen cijfers

    lower_wachtwoord = wachtwoord.lower()

    # tel het aantal unieke tekens dat gebruikt is
    # (voorkomt wachtwoorden zoals jajajajajaja of xxxxxxxxxx)
    if len(set(lower_wachtwoord)) < 5:
        return False, "Wachtwoord bevat te veel gelijke tekens"

    # detecteer herkenbare woorden en keyboard walks
    for verboden_woord in VERBODEN_WOORDEN_IN_WACHTWOORD:
        if verboden_woord in lower_wachtwoord:
            return False, "Wachtwoord is niet sterk genoeg"

    return True, None


class AccountSessions(models.Model):
    """ Speciale table om bij te houden welke sessies bij een account horen
        zodat we deze eenvoudig kunnen benaderen.
    """

    # helaas gaat dit niet met een ManyToMany relatie, dus moet het zo
    # (based on https://gavinballard.com/associating-django-users-sessions/)

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)


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
    for obj in (AccountEmail
                .objects
                .select_related('account')
                .filter(email_is_bevestigd=False,
                        bevestigde_email='',
                        account__last_login=None,
                        account__date_joined__lt=wat_ouder)):

        stdout.write('[INFO] Verwijder onvoltooid account %s' % obj.account)
        obj.account.delete()
    # for


# end of file
