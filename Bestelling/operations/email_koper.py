# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_KORT_BREAK
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS2STR,
                                   BESTELLING_TRANSPORT_OPHALEN)
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE
from Betaal.format import format_bedrag_euro
from Mailer.operations import mailer_queue_email, render_email_template
from types import SimpleNamespace
from decimal import Decimal

EMAIL_TEMPLATE_BEVESTIG_BESTELLING = 'email_bestelling/bevestig-bestelling.dtl'
EMAIL_TEMPLATE_BEVESTIG_BETALING = 'email_bestelling/bevestig-betaling.dtl'


def _beschrijf_bestelling(bestelling: Bestelling) -> list:

    regel_nr = 0

    regels = list(bestelling.regels.order_by('pk'))
    for regel in regels:
        # nieuwe regel op de bestelling
        regel_nr += 1
        regel.regel_nr = regel_nr
        regel.beschrijving = regel.korte_beschrijving.split(BESTELLING_KORT_BREAK)
        regel.bedrag_euro_str = format_bedrag_euro(regel.bedrag_euro)
    # for

    # voeg de eventuele verzendkosten toe als aparte regel op de bestelling
    if bestelling.verzendkosten_euro > 0.001:

        verzendkosten_euro_str = format_bedrag_euro(bestelling.verzendkosten_euro)

        # nieuwe regel op de bestelling
        regel_nr += 1
        regel = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=["Verzendkosten"],       # TODO: specialiseren in pakket/briefpost
                        # geen btw op transport
                        bedrag_euro_str=verzendkosten_euro_str)
        regels.append(regel)

    if bestelling.transport == BESTELLING_TRANSPORT_OPHALEN:

        nul_euro_str = format_bedrag_euro(Decimal(0))

        # nieuwe regel op de bestelling
        regel_nr += 1
        regel = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=["Ophalen op het bondsbureau"],
                        bedrag_euro_str=nul_euro_str)
        regels.append(regel)

    # formatteren van de BTW bedragen
    bestelling.btw_euro_cat1_str = format_bedrag_euro(bestelling.btw_euro_cat1)
    bestelling.btw_euro_cat2_str = format_bedrag_euro(bestelling.btw_euro_cat2)
    bestelling.btw_euro_cat3_str = format_bedrag_euro(bestelling.btw_euro_cat3)

    return regels


def _beschrijf_transacties(bestelling: Bestelling):
    transacties = (bestelling
                   .transacties
                   .all()
                   .order_by('when'))  # chronologisch

    for transactie in transacties:
        transactie.when_str = timezone.localtime(transactie.when).strftime('%Y-%m-%d om %H:%M')
        transactie.is_restitutie = (transactie.transactie_type == TRANSACTIE_TYPE_MOLLIE_RESTITUTIE)
    # for

    return transacties


def stuur_email_naar_koper_bestelling_details(bestelling: Bestelling):
    """ Stuur een e-mail naar de koper met details van de bestelling en betaalinstructies """

    account = bestelling.account

    regels = _beschrijf_bestelling(bestelling)

    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    heeft_afleveradres = False
    for nr in (1, 2, 3, 4, 5):
        regel = getattr(bestelling, 'afleveradres_regel_%s' % nr)
        if regel:
            heeft_afleveradres = True
    # for

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'regels': regels,
        'bestel_status': BESTELLING_STATUS2STR[bestelling.status],
        'kan_betalen': bestelling.status not in (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD),
        'heeft_afleveradres': heeft_afleveradres,
        'wil_ophalen': bestelling.transport == BESTELLING_TRANSPORT_OPHALEN,
    }

    if bestelling.status == BESTELLING_STATUS_NIEUW:
        context['bestel_status'] = 'Te betalen'

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BESTELLING)

    mailer_queue_email(account.bevestigde_email,
                       'Bestelling op MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


def stuur_email_naar_koper_betaalbevestiging(bestelling: Bestelling):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account

    regels = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)
    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    heeft_afleveradres = False
    for nr in (1, 2, 3, 4, 5):
        regel = getattr(bestelling, 'afleveradres_regel_%s' % nr)
        if regel:
            heeft_afleveradres = True
    # for

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'regels': regels,
        'transacties': transacties,
        'heeft_afleveradres': heeft_afleveradres,
        'wil_ophalen': bestelling.transport == BESTELLING_TRANSPORT_OPHALEN,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BETALING)

    mailer_queue_email(account.bevestigde_email,
                       'Bevestiging aankoop via MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


# end of file
