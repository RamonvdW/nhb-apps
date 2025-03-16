# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_KORT_BREAK, BESTELLING_TRANSPORT_OPHALEN
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE
from Betaal.format import format_bedrag_euro
from Functie.models import Functie
from Mailer.operations import mailer_queue_email, render_email_template
from types import SimpleNamespace
from decimal import Decimal

EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN = 'email_bestelling/backoffice-versturen.dtl'


def _get_emailadres_backoffice() -> str:
    return Functie.objects.get(rol='MWW').bevestigde_email


def _beschrijf_bestelling(bestelling: Bestelling) -> list:

    regel_nr = 0

    regels = list(bestelling.regels.order_by('code', 'pk'))
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


def stuur_email_webwinkel_backoffice(bestelling: Bestelling):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account
    sporter = account.sporter_set.first()

    regels = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)

    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    context = {
        'koper_sporter': sporter,       # bevat postadres
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'regels': regels,
        'transacties': transacties,
        'waarschuw_test_server': settings.IS_TEST_SERVER,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN)

    email = _get_emailadres_backoffice()

    mailer_queue_email(email,
                       'Verstuur webwinkel producten (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)

# end of file

