# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Mailer.operations import mailer_queue_email
from Account.models import Account, AccountVerzoekenTeller
from Overig.helpers import maak_unaccented
from TijdelijkeCodes.operations import maak_tijdelijke_code_account_email
from Mailer.operations import mailer_email_is_valide
import time


class AccountCreateError(Exception):
    """ Generic exception raised by account_create """
    pass


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


def account_create(username, voornaam, achternaam, wachtwoord, email, email_is_bevestigd):
    """ Maak een nieuw Account aan met een willekeurige naam
        Email wordt er meteen in gezet en heeft geen bevestiging nodig
    """

    if not mailer_email_is_valide(email):
        raise AccountCreateError('Dat is geen valide e-mail')

    # maak het account aan
    account, is_created = Account.objects.get_or_create(username=username)
    if not is_created:
        raise AccountCreateError('Account bestaat al')

    account.set_password(wachtwoord)
    account.first_name = voornaam
    account.last_name = achternaam
    account.unaccented_naam = maak_unaccented(voornaam + ' ' + achternaam)

    # geeft dit account een e-mail
    if email_is_bevestigd:
        account.email_is_bevestigd = True
        account.bevestigde_email = email
        account.nieuwe_email = ''
    else:
        account.email_is_bevestigd = False
        account.bevestigde_email = ''
        account.nieuwe_email = email

    account.save()

    return account


def account_check_gewijzigde_email(account):
    """ Zoek uit of dit account een nieuw email adres heeft wat nog bevestigd
        moet worden. Zoja, dan wordt er een tijdelijke URL aangemaakt en het e-mailadres terug gegeven
        waar een mailtje heen gestuurd moet worden.

        Retourneert: tijdelijke_url, nieuwe_mail_adres
                 of: None, None
    """

    if account.nieuwe_email:
        if account.nieuwe_email != account.bevestigde_email:
            # vraag om bevestiging van deze gewijzigde email
            # e-mail kan eerder overgenomen zijn uit de NHB-administratie
            # of handmatig ingevoerd zijn

            # blokkeer inlog totdat dit nieuwe e-mailadres bevestigd is
            account.email_is_bevestigd = False
            account.save(update_fields=['email_is_bevestigd'])

            # maak de url aan om het e-mailadres te bevestigen
            # extra parameters are just to make the url unique
            mailadres = account.nieuwe_email
            url = maak_tijdelijke_code_account_email(account, username=account.username, email=mailadres)
            return url, mailadres

    # geen gewijzigde email
    return None, None


def account_vraag_email_bevestiging(account, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_code_account_email(account, **kwargs)

    text_body = ("Hallo!\n\n"
                 + "Je hebt een account aangemaakt op " + settings.NAAM_SITE + ".\n"
                 + "Klik op onderstaande link om dit te bevestigen.\n\n"
                 + url + "\n\n"
                 + "Als jij dit niet was, neem dan contact met ons op via " + settings.EMAIL_BONDSBUREAU + "\n\n"
                 + "Veel plezier met de site!\n"
                 + "Het bondsbureau\n")

    mailer_queue_email(account.nieuwe_email,
                       'Aanmaken account voltooien',
                       text_body,
                       enforce_whitelist=False)     # deze mails altijd doorlaten


def account_email_bevestiging_ontvangen(account):
    """ Deze functie wordt vanuit de tijdelijke url receiver functie (zie view)
        aanroepen met account = Account object waar dit op van toepassing is
    """
    # voorkom verlies van een bevestigde email bij interne fouten
    if account.nieuwe_email != '':
        account.bevestigde_email = account.nieuwe_email
        account.nieuwe_email = ''
        account.email_is_bevestigd = True
        account.save()


def get_hour_number():
    # get the hour number since epoch

    seconds_since_epoch = time.time()
    hours_since_epoch = int(seconds_since_epoch / 3600)
    return hours_since_epoch


def account_controleer_snelheid_verzoeken(account, limiet=100):
    """ Controleer dat de verzoeken niet te snel binnen komen

        Retourneert: True als het tempo acceptabel is
                     False als het verdacht snel gaat
    """

    uur_nummer = get_hour_number()

    teller, is_created = AccountVerzoekenTeller.objects.get_or_create(account=account)

    if teller.uur_nummer != uur_nummer:
        teller.uur_nummer = uur_nummer
        teller.teller = 0

    teller.teller += 1
    teller.save(update_fields=['uur_nummer', 'teller'])

    return teller.teller <= limiet


# end of file
