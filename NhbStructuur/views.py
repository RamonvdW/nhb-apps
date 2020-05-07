# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.views import account_add_plugin_login
import logging

TEMPLATE_NHBSTRUCTUUR_IS_INACTIEF = 'nhbstructuur/is_inactief.dtl'

my_logger = logging.getLogger('NHBApps.Nhbstructuur')


def nhblid_login_plugin(request, from_ip, account):
    """ Deze functie wordt aangeroepen vanuit de Account login view
        (de koppeling wordt gelegd in NhbStructuur.apps.ready)

        Hier controleren we of het NHB lid wel in mag loggen
        ook zetten we het AccountEmail nieuwe_email veld indien nodig

        Return: None = mag wel inloggen
    """

    # zoek het NhbLid record dat bij dit account hoort
    if account.nhblid_set.all().count() == 1:
        nhblid = account.nhblid_set.all()[0]

        if not nhblid.is_actief_lid:
            # NHB lid mag geen gebruik maken van de NHB faciliteiten

            schrijf_in_logboek(account, 'Inloggen',
                               'Mislukte inlog vanaf IP %s voor inactief account %s' % (from_ip, repr(account.username)))

            my_logger.info('%s LOGIN Geblokkeerde inlog voor inactief account %s' % (from_ip, repr(account.username)))

            context = {'account': account}
            menu_dynamics(request, context, actief='inloggen')
            return render(request, TEMPLATE_NHBSTRUCTUUR_IS_INACTIEF, context)

        # neem de namen over in het account
        # zodat Account zelfstandig te gebruiken is
        if account.first_name != nhblid.voornaam or account.last_name != nhblid.achternaam:
            account.first_name = nhblid.voornaam
            account.last_name = nhblid.achternaam
            account.save()

        # kijk of het email adres gewijzigd is
        try:
            accountemail = account.accountemail_set.all()[0]
        except IndexError:
            # abnormal situations
            pass
        else:
            if accountemail.bevestigde_email != nhblid.email:
                # propageer het email adres uit de CRM data naar AccountEmail
                accountemail.nieuwe_email = nhblid.email
                accountemail.save()

    # gebruiker mag inloggen
    return None


# registreer de plugin
account_add_plugin_login(20, nhblid_login_plugin)


# end of file
