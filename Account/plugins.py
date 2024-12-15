# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from Account.operations.email import (account_check_gewijzigde_email,
                                      account_email_bevestiging_ontvangen,
                                      account_stuur_email_bevestig_nieuwe_email)
from Account.plugin_manager import account_add_plugin_login_gate
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_obfuscate_email
from Overig.helpers import get_safe_from_ip
from TijdelijkeCodes.definities import RECEIVER_BEVESTIG_EMAIL_ACCOUNT
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver
import logging


TEMPLATE_EMAIL_BEVESTIG_NIEUWE = 'account/email-bevestig-nieuwe.dtl'
TEMPLATE_EMAIL_BEVESTIG_HUIDIGE = 'account/email-bevestig-huidige.dtl'
TEMPLATE_EMAIL_BEVESTIGD = 'account/email-bevestigd.dtl'

my_logger = logging.getLogger('MH.Account')


def account_check_nieuwe_email(request, from_ip, account):
    """ detecteer wissel van e-mail in CRM; stuur bevestig verzoek mail """

    # kijk of een nieuw e-mailadres bevestigd moet worden
    ack_url, mailadres = account_check_gewijzigde_email(account)
    if ack_url:
        # schrijf in het logboek
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Inloggen",
                           activiteit="Bevestiging van nieuwe email gevraagd voor account %s" % repr(
                               account.username))

        account_stuur_email_bevestig_nieuwe_email(mailadres, ack_url)

        context = {'partial_email': mailer_obfuscate_email(mailadres)}
        return render(request, TEMPLATE_EMAIL_BEVESTIG_NIEUWE, context)

    # geen wijziging van e-mailadres - gewoon doorgaan
    return None


# skip_for_login_as=True om te voorkomen dat we een e-mail sturen door de login-as
account_add_plugin_login_gate(30, account_check_nieuwe_email, True)


def account_check_email_is_bevestigd(request, from_ip, account):
    """ voorkom login op een account totdat het e-mailadres bevestigd is """

    if not account.email_is_bevestigd:
        schrijf_in_logboek(account, 'Inloggen',
                           'Mislukte inlog vanaf IP %s voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        my_logger.info('%s LOGIN Mislukte inlog voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        # FUTURE: knop maken om een paar keer per uur een nieuwe mail te kunnen krijgen
        context = {'partial_email': mailer_obfuscate_email(account.nieuwe_email)}
        return render(request, TEMPLATE_EMAIL_BEVESTIG_HUIDIGE, context)

    # we wachten niet op bevestiging email - ga gewoon door
    return None


# skip_for_login_as=True om te voorkomen dat gaan blokkeren op een onbevestigde e-mail
account_add_plugin_login_gate(40, account_check_email_is_bevestigd, True)


def receive_bevestiging_account_email(request, account):
    """ deze functie wordt vanuit een POST context aangeroepen als een tijdelijke url gevolgd wordt
        om een email adres te bevestigen, zowel de eerste keer als wijziging van email.
            account is een Account object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """
    account_email_bevestiging_ontvangen(account)

    # schrijf in het logboek
    from_ip = get_safe_from_ip(request)

    msg = "Bevestigd vanaf IP %s voor account %s" % (from_ip, account.get_account_full_name())
    schrijf_in_logboek(account=account,
                       gebruikte_functie="Bevestig e-mail",
                       activiteit=msg)

    context = dict()
    if not request.user.is_authenticated:
        context['show_login'] = True

    context['verberg_login_knop'] = True

    return render(request, TEMPLATE_EMAIL_BEVESTIGD, context)


set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_ACCOUNT, receive_bevestiging_account_email)

# end of file
