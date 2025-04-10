# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from Account.plugin_manager import account_add_plugin_login_gate, account_add_plugin_ww_vergeten
from Logboek.models import schrijf_in_logboek
import logging

"""
    registratie van de plugins bij importeren van dit bestaand
    import in Sporter.apps.ready
"""

TEMPLATE_SPORTER_LOGIN_GEBLOKKEERD = 'sporter/login-geblokkeerd-geen-vereniging.dtl'

my_logger = logging.getLogger('MH.Sporter')


def sporter_login_plugin(request, from_ip, account):
    """ Deze functie wordt aangeroepen vanuit de Account login view

        Hier controleren we of het lid wel in mag loggen
        ook zetten we het nieuwe_email veld indien nodig
        en nemen we het 'scheids' veld over

        Return: None = mag wel inloggen
    """

    # zoek het Sporter record dat bij dit account hoort
    if account.sporter_set.all().count() == 1:
        sporter = account.sporter_set.first()

        if not (account.is_staff or account.is_BB):  # beschermt management rollen tegen CRM ongelukken
            if not sporter.is_actief_lid:
                # lid mag geen gebruik (meer) maken van de faciliteiten

                schrijf_in_logboek(account, 'Inloggen',
                                   'Mislukte inlog vanaf IP %s voor inactief account %s' % (from_ip,
                                                                                            repr(account.username)))

                my_logger.info('%s LOGIN Geblokkeerde inlog voor inactief account %s' % (from_ip,
                                                                                         repr(account.username)))

                context = {'account': account, 'verberg_login_knop': True}
                return render(request, TEMPLATE_SPORTER_LOGIN_GEBLOKKEERD, context)

        updated = list()

        # neem de namen over in het account
        # zodat Account zelfstandig te gebruiken is
        if (account.first_name != sporter.voornaam
                or account.last_name != sporter.achternaam
                or account.unaccented_naam != sporter.unaccented_naam):
            account.first_name = sporter.voornaam
            account.last_name = sporter.achternaam
            account.unaccented_naam = sporter.unaccented_naam
            updated.extend(['first_name', 'last_name', 'unaccented_naam'])

        if account.scheids != sporter.scheids:
            account.scheids = sporter.scheids
            updated.append('scheids')

        # kijk of het email adres gewijzigd is
        if account.bevestigde_email != sporter.email:
            # propageer het email adres uit de CRM data naar het Account
            account.nieuwe_email = sporter.email
            updated.append('nieuwe_email')

        if len(updated):
            account.save(update_fields=updated)

    # gebruiker mag inloggen
    return None


# registreer de plugin
account_add_plugin_login_gate(20, sporter_login_plugin, False)


def sporter_ww_vergeten_plugin(_request, _from_ip, account):
    """ Deze functie wordt aangeroepen vanuit de Account wachtwoord vergeten view
        Hier zetten we een eventueel aangepast e-mailadres uit het CRM door naar het account.
    """

    # zoek het Sporter record dat bij dit account hoort
    if account.sporter_set.all().count() == 1:
        sporter = account.sporter_set.first()

        if not (account.is_staff or account.is_BB):  # beschermt management rollen tegen CRM ongelukken
            if not sporter.is_actief_lid:
                # lid mag geen gebruik (meer) maken van de faciliteiten
                return

        # propageer een eventueel nieuw email adres uit de CRM data naar het Account
        if account.bevestigde_email != sporter.email:
            account.nieuwe_email = sporter.email
            account.save(update_fields=['nieuwe_email'])


# registreer de plugin
account_add_plugin_ww_vergeten(20, sporter_ww_vergeten_plugin)


# end of file
