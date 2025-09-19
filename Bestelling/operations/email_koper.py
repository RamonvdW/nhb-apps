# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_KORT_BREAK, BESTELLING_TRANSPORT2STR
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS2STR,
                                   BESTELLING_TRANSPORT_OPHALEN, BESTELLING_TRANSPORT_VERZEND)
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE
from Betaal.format import format_bedrag_euro
from Mailer.operations import mailer_queue_email, render_email_template
from Vereniging.models import Vereniging

EMAIL_TEMPLATE_BEVESTIG_BESTELLING = 'email_bestelling/bevestig-bestelling.dtl'
EMAIL_TEMPLATE_BEVESTIG_BETALING = 'email_bestelling/bevestig-betaling.dtl'


def _beschrijf_transport(bestelling: Bestelling, context: dict):

    if bestelling.transport == BESTELLING_TRANSPORT_OPHALEN:
        ophalen_ver = Vereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)
        context['wil_ophalen'] = True
        context['ophalen_adres_regel_1'] = ophalen_ver.adres_regel1
        context['ophalen_adres_regel_2'] = ophalen_ver.adres_regel2

    elif bestelling.transport == BESTELLING_TRANSPORT_VERZEND:
        afleveradres = [regel
                        for regel in (bestelling.afleveradres_regel_1, bestelling.afleveradres_regel_2,
                                      bestelling.afleveradres_regel_3, bestelling.afleveradres_regel_4,
                                      bestelling.afleveradres_regel_5)
                        if regel]
        if len(afleveradres) == 0:
            afleveradres.append('Probleem: adres is niet bekend!')
        context['afleveradres'] = afleveradres
        context['heeft_afleveradres'] = True


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


def stuur_email_naar_koper_bestelling_details(stdout, bestelling: Bestelling):
    """ Stuur een e-mail naar de koper met details van de bestelling en betaalinstructies """

    account = bestelling.account

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': format_bedrag_euro(bestelling.totaal_euro),
        'regels': _beschrijf_bestelling(bestelling),
        'bestel_status': BESTELLING_STATUS2STR[bestelling.status],
        'kan_betalen': bestelling.status not in (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD),
    }

    _beschrijf_transport(bestelling, context)

    if bestelling.status == BESTELLING_STATUS_NIEUW:
        context['bestel_status'] = 'Te betalen'

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BESTELLING)

    mailer_queue_email(account.bevestigde_email,
                       'Bestelling op MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)

    stdout.write('[INFO] E-mail naar koper met details van bestelling %s is verstuurd' % bestelling.mh_bestel_nr())


def stuur_email_naar_koper_betaalbevestiging(stdout, bestelling: Bestelling):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': format_bedrag_euro(bestelling.totaal_euro),
        'regels': _beschrijf_bestelling(bestelling),
        'transacties': _beschrijf_transacties(bestelling),
    }

    _beschrijf_transport(bestelling, context)

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BETALING)

    mailer_queue_email(account.bevestigde_email,
                       'Bevestiging aankoop via MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)

    stdout.write('[INFO] E-mail naar koper met betaalbevestiging van bestelling %s is verstuurd' %
                 bestelling.mh_bestel_nr())


# end of file
