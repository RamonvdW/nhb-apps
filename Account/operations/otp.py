# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Account.models import Account, AccountSessions, get_account
from Account.operations.session_vars import zet_sessionvar_if_changed
from Account.plugin_manager import account_plugins_otp_was_reset
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Mailer.operations import mailer_queue_email, render_email_template
import logging
import pyotp

SESSIONVAR_ACCOUNT_OTP_CONTROL_IS_GELUKT = "account_otp_verified"

EMAIL_TEMPLATE_OTP_IS_LOSGEKOPPELD = 'email_account/otp-is-losgekoppeld.dtl'

my_logger = logging.getLogger('MH.Account')


def otp_zet_controle_niet_gelukt(request) -> bool:
    """ Deze functie wordt aangeroepen vanuit de LoginAsView en WachtenVergetenView
        om een sessie variabele te zetten die onthoudt dat de gebruiker geen OTP controle
        gedaan heeft.

        Return value:
            True:  OTP controle vlag is aangepast
            False: OTP controle vlag stond al goed
    """

    account = get_account(request)

    changed = zet_sessionvar_if_changed(request, SESSIONVAR_ACCOUNT_OTP_CONTROL_IS_GELUKT, False)

    # zorg dat nieuwe sessies al aangemaakt zijn
    if not request.session.session_key:     # pragma: no cover
        request.session.save()

    # koppel de (eventuele nieuwe) sessie aan het account
    AccountSessions.objects.get_or_create(account=account,
                                          session_id=request.session.session_key)   # session_id = primary key

    # geef de OTP reset door
    for notify in account_plugins_otp_was_reset:
        notify(request)
    # for

    return changed


def otp_zet_controle_gelukt(request):
    """ Deze functie wordt aangeroepen vanuit de OTPControleView en OTPKoppelenView om een sessie variabele
        te zetten die onthoudt dat de OTP-controle voor de gebruiker gelukt is
    """
    account = get_account(request)
    account.otp_controle_gelukt_op = timezone.now()
    account.save(update_fields=['otp_controle_gelukt_op'])

    zet_sessionvar_if_changed(request, SESSIONVAR_ACCOUNT_OTP_CONTROL_IS_GELUKT, True)


def otp_is_controle_gelukt(request):
    """
        Geef aan of de OTP control gelukt is
        Returns: True  = OTP control is uitgevoerd en gelukt
                 False = OTP control niet gelukt
    """
    try:
        return request.session[SESSIONVAR_ACCOUNT_OTP_CONTROL_IS_GELUKT]
    except KeyError:
        pass
    return False


def otp_prepare_koppelen(account: Account):
    """ Als het account nog niet voorbereid is voor OTP, maak het dan in orde
    """
    # maak eenmalig het OTP geheim aan voor deze gebruiker
    if len(account.otp_code) not in (16, 32):
        account.otp_code = pyotp.random_base32()[:32]
        account.save(update_fields=['otp_code'])


def otp_koppel_met_code(request, account, code):
    """ Breng de OTP koppeling tot stand als de juiste code opgegeven is

        als deze klopt, dan wordt koppeling vastgelegd en extra rechten vrijgegeven
        als de control mislukt, dan wordt dit in het logboek geschreven

        Returns: True:  Gelukt
                 False: Mislukt
    """
    if not request.user.is_authenticated:
        return False

    from_ip = get_safe_from_ip(request)

    otp = pyotp.TOTP(account.otp_code)
    # valid_window=1 staat toe dat er net een nieuwe code gegenereerd is tijdens het intikken van de code
    is_valid = otp.verify(code, valid_window=1)

    if is_valid:
        # controle is gelukt --> koppeling maken
        account.otp_is_actief = True
        account.save(update_fields=['otp_is_actief'])
        my_logger.info('%s 2FA koppeling gelukt voor account %s' % (from_ip, account.username))

        otp_zet_controle_gelukt(request)
        return True

    # controle is mislukt - schrijf dit in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="OTP controle",
                       activiteit='Gebruiker %s OTP koppeling controle mislukt vanaf IP %s' % (
                            repr(account.username), from_ip))
    my_logger.info('%s 2FA koppeling mislukte controle voor account %s' % (from_ip, account.username))
    return False


def otp_controleer_code(request, account, code):
    """ deze functie controleert de opgegeven account code
        als deze klopt, dan worden extra rechten vrijgegeven
        als de control mislukt, dan wordt dit in het logboek geschreven

        Returns: True:  Gelukt
                 False: Mislukt
    """
    if not request.user.is_authenticated:
        return False

    if not account.otp_is_actief:
        return False

    from_ip = get_safe_from_ip(request)

    otp = pyotp.TOTP(account.otp_code)
    # valid_window=1 staat toe dat er net een nieuwe code gegenereerd is tijdens het intikken van de code
    is_valid = otp.verify(code, valid_window=1)

    if is_valid:
        # controle is gelukt
        otp_zet_controle_gelukt(request)
        my_logger.info('%s 2FA controle gelukt voor account %s' % (from_ip, account.username))
        return True

    # controle is mislukt - schrijf dit in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="OTP controle",
                       activiteit='Gebruiker %s OTP controle mislukt vanaf IP %s' % (repr(account.username), from_ip))
    my_logger.info('%s 2FA mislukt voor account %s met code %s' % (from_ip, account.username, repr(code)))
    return False


def otp_loskoppelen(request, account):
    """ Koppelde de tweede factor los voor het gevraagde account

        Geeft True terug als OTP actief was en echt losgekoppeld is.
    """

    # control dat gebruiker genoeg rechten heeft moet door aanroeper gedaan zijn
    if not request.user.is_authenticated:
        return False

    if not account.otp_is_actief:
        return False

    from_ip = get_safe_from_ip(request)

    account.otp_is_actief = False
    account.save(update_fields=['otp_is_actief'])
    my_logger.info('%s 2FA losgekoppeld voor account %s' % (from_ip, account.username))

    # schrijf in het logboek
    door_account = get_account(request)
    schrijf_in_logboek(account=door_account,
                       gebruikte_functie="OTP loskoppelen",
                       activiteit='OTP is losgekoppeld voor gebruiker %s' % account.username)
    return True


def otp_stuur_email_losgekoppeld(account):

    """ Stuur een e-mail naar 'account' om te melden dat de OTP losgekoppeld is """

    context = {
        'voornaam': account.get_first_name(),
        'contact_email': settings.EMAIL_BONDSBUREAU,
        'url_handleiding_beheerders': settings.URL_PDF_HANDLEIDING_BEHEERDERS
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_OTP_IS_LOSGEKOPPELD)

    mailer_queue_email(account.bevestigde_email,
                       'Tweede factor losgekoppeld op ' + settings.NAAM_SITE,
                       mail_body)

# end of file
