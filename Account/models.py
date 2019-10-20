# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from NhbStructuur.models import NhbLid
from Overig.tijdelijke_url import maak_tijdelijke_url_accountemail, set_tijdelijke_url_receiver, RECEIVER_ACCOUNTEMAIL


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
    # (inherited, not used) last_name
    # (inherited, not used) email
    # (inherited) user_permissions: ManyToMany
    # (inherited) groups: ManyToMany
    is_voltooid = models.BooleanField(
                        default=False,
                        help_text="Extra informatie correct opgegeven voor NHB account?")
    extra_info_pogingen = models.IntegerField(
                                default=3,
                                help_text="Aantal pogingen over om extra informatie voor NHB account op te geven")
    vraag_nieuw_wachtwoord = models.BooleanField(
                                    default=False,
                                    help_text="Moet de gebruiker een nieuw wachtwoord opgeven bij volgende inlog?")

    REQUIRED_FIELDS = ['password']

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def get_first_name(self):
        """ Deze functie wordt aangeroepen als user.get_first_name
            gebruikt wordt in een template
        """
        # TODO: werkt dit ook nog goed voor niet-NHB leden die een email als username hebben?
        return self.first_name or self.username


class AccountEmail(models.Model):
    """ definitie van een email adres (en de status daarvan) voor een account """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # email
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
        return "Email voor account '%s' (%s)" % (self.account.username,
                                                 self.bevestigde_email)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "AccountEmail"
        verbose_name_plural = "AccountEmails"


class LogboekRegel(models.Model):
    """ definitie van een regel in het logboek """
    toegevoegd_op = models.DateTimeField()
    actie_door_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    gebruikte_functie = models.CharField(max_length=100)
    activiteit = models.CharField(max_length=500)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s [%s] %s: %s" % (str(self.toegevoegd_op),
                                   self.actie_door_account.login_naam,
                                   self.gebruikte_functie,
                                   self.activiteit)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Logboek regel"
        verbose_name_plural = "Logboek regels"


class HanterenPersoonsgegevens(models.Model):
    """ status van de vraag om juist om te gaan met persoonsgegevens,
        voor accounts waarvoor dit relevant is.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    acceptatie_datum = models.DateTimeField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s [%s]" % (str(self.acceptatie_datum),
                            self.account.login_naam)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Hanteren Persoonsgegevens"
        verbose_name_plural = "Hanteren Persoonsgegevens"


def is_email_valide(adres):
    """ Basic check of dit een valide email adres is:
        - niet leeg
        - bevat @
        - bevat geen spatie
        - domein bevat een .
        Uiteindelijk weet je pas of het een valide adres is als je er een email naartoe kon sturen
        We proberen lege velden en velden met opmerkingen als "geen" of "niet bekend" te ontdekken.
    """
    if adres and len(adres) >= 4 and '@' in adres and ' ' not in adres and r'\t' not in adres:
        user, domein = adres.rsplit('@', 1)
        if '.' in domein:
            return True
    return False


def account_create_username_wachtwoord_email(username, wachtwoord, email):
    """ Maak een nieuw account aan met een willekeurige naam
        Email wordt er meteen in gezet en heeft geen bevestiging nodig
    """

    if not is_email_valide(email):
        raise AccountCreateError('Dat is geen valide email')

    # maak het account aan
    account = Account()
    account.username = username
    account.set_password(wachtwoord)
    account.save()

    # maak het email record aan
    mail = AccountEmail()
    mail.account = account
    mail.email_is_bevestigd = True
    mail.bevestigde_email = email
    mail.nieuwe_email = email
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
        raise AccountCreateError('Onbekend NHB nummmer')

    try:
        nhblid = NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        raise AccountCreateError('Onbekend NHB nummer')

    if not is_email_valide(nhblid.email):
        raise AccountCreateError('Account heeft geen email adres. Neem contact op met de secretaris van je vereniging.')
        # TODO: dit moeten gaan loggen
        # TODO: redirect naar de secretaris?

    if email != nhblid.email:
        raise AccountCreateError('De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    # maak het account aan
    account = Account()
    account.username = nhb_nummer
    account.set_password(nieuw_wachtwoord)
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
    mail.email_is_bevestigd = True
    mail.save()

# end of file
