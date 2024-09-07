# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import login
from Account.operations.otp import otp_zet_controle_niet_gelukt
from Functie.rol import rol_bepaal_beschikbare_rollen
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
import logging

my_logger = logging.getLogger('MH.Account')


def auto_login_gast_account(request, account):
    """ automatisch inlog op een nieuw account; wordt gebruikt voor aanmaken gast-account.
    """
    # integratie met de authenticatie laag van Django
    login(request, account)

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog voor gast-account %s' % (
                        from_ip, repr(account.username)))

    # we slaan de typische plug-ins over omdat we geen pagina of redirect kunnen doorgeven

    otp_zet_controle_niet_gelukt(request)

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog op gast-account %s vanaf IP %s" % (
                                        repr(account.get_account_full_name()), from_ip))

    # zorg dat de rollen goed ingesteld staan
    rol_bepaal_beschikbare_rollen(request, account)


# end of file
