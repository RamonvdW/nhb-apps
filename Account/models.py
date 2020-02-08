# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from NhbStructuur.models import NhbLid
from Overig.tijdelijke_url import maak_tijdelijke_url_accountemail, set_tijdelijke_url_receiver, RECEIVER_ACCOUNTEMAIL
from BasisTypen.models import BoogType
import datetime
import pyotp


SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED = "account_otp_verified"


class AccountCreateError(Exception):
    """ Generic exception raised by account_create_nhb """
    pass


class AccountCreateNhbGeenEmail(Exception):
    """ Specifieke foutmelding omdat het NHB lid geen e-mail adres heeft """
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
    # (inherited, not used) last_name
    # (inherited, not used) e-mail
    # (inherited) user_permissions: ManyToMany
    # (inherited) groups: ManyToMany
    vraag_nieuw_wachtwoord = models.BooleanField(   # TODO: implement
                                    default=False,
                                    help_text="Moet de gebruiker een nieuw wachtwoord opgeven bij volgende inlog?")

    # optionele koppeling met NhbLid
    # (niet alle Accounts zijn NHB lid)
    nhblid = models.ForeignKey(NhbLid, on_delete=models.PROTECT,
                               blank=True,  # allow access input in form
                               null=True)   # allow NULL relation in database

    laatste_inlog_poging = models.DateTimeField(blank=True, null=True)

    # verkeerd wachtwoord opgegeven via login of wijzig-wachtwoord
    verkeerd_wachtwoord_teller = models.IntegerField(
                                    default=0,
                                    help_text="Aantal mislukte inlog pogingen op rij")

    is_geblokkeerd_tot = models.DateTimeField(
                                    blank=True, null=True,
                                    help_text="Login niet mogelijk tot")

    is_BKO = models.BooleanField(
                        default=False,
                        help_text="BK Organisator")

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
        if self.nhblid:
            return self.nhblid.voornaam
        # TODO: werkt dit ook nog goed voor niet-NHB leden die een e-mail als username hebben?
        return self.first_name or self.username

    def volledige_naam(self):
        if self.nhblid:
            return self.nhblid.volledige_naam()
        return self.username

    def get_account_full_name(self):
        """ Deze functie wordt aangeroepen vanuit de site feedback om een volledige
            referentie aan de gebruiker te krijgen.
            Vanuit template: user.get_account_full_name
        """
        if self.nhblid:
            return "%s %s (%s)" % (self.nhblid.voornaam, self.nhblid.achternaam, self.username)
        return self.username


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


def account_needs_vhpg(account):
    """ Controlleer of het Account een VHPG af moet leggen """

    if not account_needs_otp(account):
        # niet nodig
        return False, None

    # kijk of de acceptatie recent al afgelegd is
    try:
        vhpg = HanterenPersoonsgegevens.objects.get(account=account)
    except HanterenPersoonsgegevens.DoesNotExist:
        # niet uitgevoerd, wel nodig
        return True, None

    # elke 11 maanden moet de verklaring afgelegd worden
    # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
    next = vhpg.acceptatie_datum + datetime.timedelta(days=334)
    now = timezone.now()
    return next < now, vhpg


def account_vhpg_is_geaccepteerd(account):
    """ onthoud dat de vhpg net geaccepteerd is door de gebruiker
    """
    try:
        vhpg = HanterenPersoonsgegevens.objects.get(account=account)
    except HanterenPersoonsgegevens.DoesNotExist:
        vhpg = HanterenPersoonsgegevens()
        vhpg.account = account

    vhpg.acceptatie_datum = timezone.now()
    vhpg.save()


class SchutterBoog(models.Model):
    """ voor elk type boog waar de schutter interesse in heeft is er een record """

    # het account waar dit record bij hoort
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # voorkeuren van de schutter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=False)
    voor_wedstrijd = models.BooleanField(default=False)

    # voorkeur voor DT (alleen voor Recurve)
    voorkeur_dutchtarget_18m = models.BooleanField(default=False)


def is_email_valide(adres):
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

    if not is_email_valide(email):
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


def account_create_nhb(nhb_nummer, email, nieuw_wachtwoord):
    """ Maak een nieuw account aan voor een NHB lid
        raises AccountError als:
            - er al een account bestaat
            - het nhb nummer niet valide is
            - het email adres niet bekend is bij de nhb
            - het email adres niet overeen komt
        geeft de url terug die in de email verstuurd moet worden
    """
    if Account.objects.filter(username=nhb_nummer).count() != 0:
        raise AccountCreateError('Account bestaat al')

    # zoek het email adres van dit NHB lid erbij
    try:
        nhb_nr = int(nhb_nummer)
    except ValueError:
        raise AccountCreateError('Onbekend NHB nummer')

    try:
        nhblid = NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        raise AccountCreateError('Onbekend NHB nummer')

    if not is_email_valide(nhblid.email):
        raise AccountCreateNhbGeenEmail()

    if email != nhblid.email:
        raise AccountCreateError('De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    # maak het account aan
    account = Account()
    account.username = nhb_nummer
    account.set_password(nieuw_wachtwoord)
    account.nhblid = nhblid
    account.save()

    # maak het email record aan
    mail = AccountEmail()
    mail.account = account
    mail.email_is_bevestigd = False
    mail.bevestigde_email = ''
    mail.nieuwe_email = email
    mail.save()

    # maak de url aan om het emailadres te bevestigen
    url = maak_tijdelijke_url_accountemail(mail, nhb_nummer=nhb_nummer, email=email)
    return url


def account_email_is_bevestigd(mail):
    """ Deze functie wordt vanuit de tijdelijke url receiver functie (zie view)
        aanroepen met mail = AccountEmail object waar dit op van toepassing is
    """
    mail.bevestigde_email = mail.nieuwe_email
    mail.nieuwe_email = ''
    mail.email_is_bevestigd = True
    mail.save()


def account_needs_otp(account):
    """ Controleer of het Account OTP verificatie nodig heeft

        Returns: True or False
        Bepaalde rechten vereisen OTP:
            is_BKO
            is_staff
            rechten voor beheerders
    """
    if account.is_BKO or account.is_staff:
        return True

    for group in account.groups.all():
        if group.name[:4] in ("BKO ", "RKO ", "RCL ", "CWZ "):
            return True

    return False


def account_is_otp_gekoppeld(account):
    return account.otp_is_actief


def account_prep_for_otp(account):
    """ Als het account nog niet voorbereid is voor OTP, maak het dan in orde
    """
    # maak eenmalig het OTP geheim aan voor deze gebruiker
    if len(account.otp_code) != 16:
        account.otp_code = pyotp.random_base32()
        account.save()


def account_controleer_otp_code(account, code):
    otp = pyotp.TOTP(account.otp_code)
    # valid_window=1 staat toe dat er net een nieuwe code gegenereerd is tijdens het intikken van de code
    return otp.verify(code, valid_window=1)


def account_zet_sessionvars_na_login(request):
    """ Deze functie wordt aangeroepen vanuit de LoginView om een sessie variabele
        te zetten die onthoudt of de gebruiker een OTP controle uitgevoerd heeft
    """
    sessionvars = request.session
    sessionvars[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED] = False
    return sessionvars  # allows unittest to do sessionvars.save()


def account_zet_sessionvars_na_otp_controle(request):
    """ Deze functie wordt aangeroepen vanuit de OTPControleView om een sessie variabele
        te zetten die onthoudt dat de OTP controle voor de gebruiker gelukt is
    """
    sessionvars = request.session
    sessionvars[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED] = True
    return sessionvars  # allows unittest to do sessionvars.save()


def user_is_otp_verified(request):
    try:
        return request.session[SESSIONVAR_ACCOUNT_IS_OTP_VERIFIED]
    except KeyError:
        pass
    return False


# end of file
