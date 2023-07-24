# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Mailer.operations import mailer_queue_email, render_email_template
from TijdelijkeCodes.operations import maak_tijdelijke_code_bevestig_email_account


EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL = 'email_account/bevestig-toegang-email.dtl'


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
            # e-mail kan eerder overgenomen zijn uit het CRM systeem
            # of handmatig ingevoerd zijn

            # blokkeer inlog totdat dit nieuwe e-mailadres bevestigd is
            account.email_is_bevestigd = False
            account.save(update_fields=['email_is_bevestigd'])

            # maak de url aan om het e-mailadres te bevestigen
            # extra parameters are just to make the url unique
            mailadres = account.nieuwe_email
            url = maak_tijdelijke_code_bevestig_email_account(account, username=account.username, email=mailadres)
            return url, mailadres

    # geen gewijzigde email
    return None, None


def account_stuur_email_bevestig_nieuwe_email(mailadres, ack_url):
    """ Stuur een mail om toegang tot het (gewijzigde) e-mailadres te bevestigen """

    context = {
        'naam_site': settings.NAAM_SITE,
        'url': ack_url,
        'contact_email': settings.EMAIL_BONDSBUREAU
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL)

    mailer_queue_email(mailadres,
                       'Email adres bevestigen',
                       mail_body,
                       enforce_whitelist=False)


def account_email_bevestiging_ontvangen(account):
    """ Deze functie wordt vanuit de tijdelijke url receiver aangeroepen, via onze plugin.py
        met account = Account object waar dit op van toepassing is
    """
    # voorkom verlies van een bevestigde email bij interne fouten
    if account.nieuwe_email != '':
        account.bevestigde_email = account.nieuwe_email     # TODO: geen garantie dat dit de bevestigde e-mail is!
        account.nieuwe_email = ''
        account.email_is_bevestigd = True
        account.save(update_fields=['bevestigde_email', 'nieuwe_email', 'email_is_bevestigd'])


# end of file
