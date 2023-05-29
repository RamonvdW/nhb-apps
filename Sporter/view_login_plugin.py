# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.contrib.auth import logout
from Account.views import account_add_plugin_login
from Logboek.models import schrijf_in_logboek
from Plein.menu import menu_dynamics
import logging


TEMPLATE_NHBSTRUCTUUR_IS_INACTIEF = 'sporter/is_inactief.dtl'

my_logger = logging.getLogger('NHBApps.Sporter')


def sporter_login_plugin(request, from_ip, account):
    """ Deze functie wordt aangeroepen vanuit de Account login view
        (de koppeling wordt gelegd in Sporter.apps.ready)

        Hier controleren we of het NHB lid wel in mag loggen
        ook zetten we het AccountEmail nieuwe_email veld indien nodig

        Return: None = mag wel inloggen
    """

    # zoek het Sporter record dat bij dit account hoort
    if account.sporter_set.all().count() == 1:
        sporter = account.sporter_set.all()[0]

        if not (account.is_staff or account.is_BB):  # beschermt management rollen tegen CRM ongelukken
            if not sporter.is_actief_lid:
                # NHB lid mag geen gebruik maken van de NHB faciliteiten

                schrijf_in_logboek(account, 'Inloggen',
                                   'Mislukte inlog vanaf IP %s voor inactief account %s' % (from_ip, repr(account.username)))

                my_logger.info('%s LOGIN Geblokkeerde inlog voor inactief account %s' % (from_ip, repr(account.username)))

                context = {'account': account, 'verberg_login_knop': True}

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(request)

                menu_dynamics(request, context)
                return render(request, TEMPLATE_NHBSTRUCTUUR_IS_INACTIEF, context)

        # neem de namen over in het account
        # zodat Account zelfstandig te gebruiken is
        if (account.first_name != sporter.voornaam
                or account.last_name != sporter.achternaam
                or account.unaccented_naam != sporter.unaccented_naam):
            account.first_name = sporter.voornaam
            account.last_name = sporter.achternaam
            account.unaccented_naam = sporter.unaccented_naam
            account.save(update_fields=['first_name', 'last_name', 'unaccented_naam'])

        # kijk of het email adres gewijzigd is
        try:
            accountemail = account.accountemail_set.all()[0]
        except IndexError:
            # abnormal situations
            pass
        else:
            if accountemail.bevestigde_email != sporter.email:
                # propageer het email adres uit de CRM data naar AccountEmail
                accountemail.nieuwe_email = sporter.email
                accountemail.save()

    # gebruiker mag inloggen
    return None


# registreer de plugin
account_add_plugin_login(20, sporter_login_plugin, False)


# end of file