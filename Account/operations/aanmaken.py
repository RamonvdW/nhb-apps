# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.models import Account
from Overig.helpers import maak_unaccented
from Mailer.operations import mailer_email_is_valide


class AccountCreateError(Exception):
    """ Generic exception raised by account_create """
    pass


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


# end of file
