# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Webwinkel """

from django.conf import settings
from Bestelling.definities import BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_VERZEND
from Betaal.format import format_bedrag_euro
from Webwinkel.definities import KEUZE_STATUS_GEANNULEERD, VERZENDKOSTEN_BRIEFPOST, VERZENDKOSTEN_PAKKETPOST
from decimal import Decimal


def webwinkel_plugin_beschrijf_product(keuze):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """
    beschrijving = list()

    product = keuze.product

    msg = product.omslag_titel
    if product.kleding_maat:
        msg += ', maat %s' % product.kleding_maat
    tup = ('Titel', msg)
    beschrijving.append(tup)

    tup = ('Prijs per stuk', format_bedrag_euro(product.prijs_euro))
    beschrijving.append(tup)

    if product.eenheid:
        if ',' in product.eenheid:
            aantal_enkel, aantal_meer = product.eenheid.split(',')
        else:
            aantal_enkel = aantal_meer = product.eenheid
    else:
        aantal_enkel = aantal_meer = 'stuks'

    aantal_str = str(keuze.aantal) + ' '
    if keuze.aantal > 1:
        aantal_str += aantal_meer
    else:
        aantal_str += aantal_enkel

    if product.bevat_aantal > 1:
        aantal_str += " van %s" % product.bevat_aantal

    tup = ('Aantal', aantal_str)
    beschrijving.append(tup)

    return beschrijving


def webwinkel_plugin_bepaal_verzendkosten_mandje(stdout, mandje):
    """ bereken de verzendkosten voor fysieke producten in het mandje """

    webwinkel_count = 0
    webwinkel_briefpost = 0
    webwinkel_pakketpost = 0
    for product in mandje.producten.select_related('webwinkel_keuze__product').all():
        if product.webwinkel_keuze:
            webwinkel_count += 1

            if product.webwinkel_keuze.product.type_verzendkosten == VERZENDKOSTEN_BRIEFPOST:
                webwinkel_briefpost += 1

            if product.webwinkel_keuze.product.type_verzendkosten == VERZENDKOSTEN_PAKKETPOST:
                webwinkel_pakketpost += 1
    # for

    mandje.verzendkosten_euro = Decimal(0)

    if webwinkel_count > 0:
        # wel fysieke producten
        if mandje.transport == BESTELLING_TRANSPORT_NVT:
            # bij toevoegen eerste product schakelen we over op verzenden
            mandje.transport = BESTELLING_TRANSPORT_VERZEND

        if mandje.transport == BESTELLING_TRANSPORT_VERZEND:
            # zet de kosten voor het verzenden (ophalen is gratis)
            if webwinkel_briefpost > 0:
                mandje.verzendkosten_euro = Decimal(settings.WEBWINKEL_BRIEF_VERZENDKOSTEN_EURO)

            if webwinkel_pakketpost > 0:
                mandje.verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_GROOT_VERZENDKOSTEN_EURO)
    else:
        # geen verzendkosten
        mandje.transport = BESTELLING_TRANSPORT_NVT

    mandje.save(update_fields=['verzendkosten_euro', 'transport'])


def webwinkel_plugin_bepaal_verzendkosten_bestelling(stdout, transport, bestelling):
    """ bereken de verzendkosten voor fysieke producten in het mandje """

    webwinkel_count = 0
    webwinkel_briefpost = 0
    webwinkel_pakketpost = 0
    for product in bestelling.producten.select_related('webwinkel_keuze__product').all():
        if product.webwinkel_keuze:
            webwinkel_count += 1

            if product.webwinkel_keuze.product.type_verzendkosten == VERZENDKOSTEN_BRIEFPOST:
                webwinkel_briefpost += 1

            if product.webwinkel_keuze.product.type_verzendkosten == VERZENDKOSTEN_PAKKETPOST:
                webwinkel_pakketpost += 1
    # for

    if webwinkel_count == 0:
        transport = BESTELLING_TRANSPORT_NVT

    bestelling.transport = transport

    if transport == BESTELLING_TRANSPORT_VERZEND:
        # wel verzendkosten
        if webwinkel_briefpost > 0:
            bestelling.verzendkosten_euro = Decimal(settings.WEBWINKEL_BRIEF_VERZENDKOSTEN_EURO)

        if webwinkel_pakketpost > 0:
            bestelling.verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_GROOT_VERZENDKOSTEN_EURO)
    else:
        # geen verzendkosten
        bestelling.verzendkosten_euro = Decimal(0)

    bestelling.save(update_fields=['verzendkosten_euro', 'transport'])


# end of file
