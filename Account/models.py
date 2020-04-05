# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from Overig.tijdelijke_url import set_tijdelijke_url_receiver, maak_tijdelijke_url_accountemail
from Account.rechten import account_rechten_otp_controle_gelukt
import datetime



class AccountCreateError(Exception):
    """ Generic exception raised by account_create_nhb """
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
    vraag_nieuw_wachtwoord = models.BooleanField(   # TODO: implement
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
                        max_length=16,          # 16-char base32 encoded secret
                        default="",
                        help_text ="OTP code")

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
        # TODO: werkt dit ook nog goed voor niet-NHB leden die een e-mail als username hebben?
        return self.first_name or self.username

    def volledige_naam(self):
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

    def get_real_name(self):
        """ Deze functie geeft de volledige naam van de gebruiker terug, indien beschikbaar.

            Wordt gebruikt vanuit djangosaml2idp
            in settings.py staat de referentie naar deze methode naam
        """
        # TODO: djangosaml2idp get_real_name herzien
        return self.volledige_naam()

    def get_email(self):
        """ helper om de email van de gebruiker te krijgen voor djangosaml2idp
            zodat deze doorgegeven kan worden aan een Service Provider zoals de Wiki server
        """
        if len(self.accountemail_set.all()) == 1:
            email = self.accountemail_set.all()[0].bevestigde_email
        else:
            email = ""
        return email


class AccountEmail(models.Model):
    """ definitie van een e-mail adres (en de status daarvan) voor een account """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # e-mail
    email_is_bevestigd = models.BooleanField(default=False)
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


class HanterenPersoonsgegevens(models.Model):
    """ status van de vraag om juist om te gaan met persoonsgegevens,
        voor de paar accounts waarvoor dit relevant is.
    """

    # het account waar dit record bij hoort
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # datum waarop de acceptatie voor het laatste gedaan is
    acceptatie_datum = models.DateTimeField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s [%s]" % (str(self.acceptatie_datum),
                            self.account.username)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Hanteren Persoonsgegevens"
        verbose_name_plural = "Hanteren Persoonsgegevens"


def account_is_email_valide(adres):
    """ Basic check of dit een valide e-mail adres is:
        - niet leeg
        - bevat @
        - bevat geen spatie
        - domein bevat een .
        Uiteindelijk weet je pas of het een valide adres is als je er een e-mail naartoe kon sturen
        We proberen lege velden en velden met opmerkingen als "geen" of "niet bekend" te ontdekken.
    """
    # full rules: https://stackoverflow.com/questions/2049502/what-characters-are-allowed-in-an-email-address
    if adres and len(adres) >= 4 and '@' in adres and ' ' not in adres:
        for char in ('\t', '\n', '\r'):
            if char in adres:
                return False
        user, domein = adres.rsplit('@', 1)
        if '.' in domein:
            return True
    return False


def account_create(username, wachtwoord, email, voornaam):
    """ Maak een nieuw Account aan met een willekeurige naam
        Email wordt er meteen in gezet en heeft geen bevestiging nodig
    """

    if not account_is_email_valide(email):
        raise AccountCreateError('Dat is geen valide e-mail')

    if Account.objects.filter(username=username).count() != 0:
        raise AccountCreateError('Account bestaat al')

    # maak het account aan
    account = Account()
    account.username = username
    account.set_password(wachtwoord)
    account.first_name = voornaam
    account.save()

    # maak het email record aan
    mail = AccountEmail()
    mail.account = account
    mail.email_is_bevestigd = True
    mail.bevestigde_email = email
    mail.nieuwe_email = ''
    mail.save()


def account_email_is_bevestigd(mail):
    """ Deze functie wordt vanuit de tijdelijke url receiver functie (zie view)
        aanroepen met mail = AccountEmail object waar dit op van toepassing is
    """
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

    if len(account.accountemail_set.all()) == 1:
        email = account.accountemail_set.all()[0]

        if email.nieuwe_email:
            if email.nieuwe_email != email.bevestigde_email:
                # vraag om bevestiging van deze gewijzgde email
                # email kan eerder overgenomen zijn uit de NHB administratie
                # of handmatig ingevoerd zijn

                # maak de url aan om het emailadres te bevestigen
                # extra parameters are just to make the url unique
                mail = email.nieuwe_email
                url = maak_tijdelijke_url_accountemail(email, username=account.username, email=mail)
                return url, mail

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


# end of file
