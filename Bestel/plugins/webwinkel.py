# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Webwinkel, zoals kortingen. """

from django.conf import settings
from django.utils.formats import localize
from decimal import Decimal


def webwinkel_plug_reserveren(webwinkel_keuze):
    """
        Deze functie wordt vanuit de achtergrondtaak aangeroepen om een product te reserveren.
        Dit hoort bij het toevoegen aan het mandje.
    """

    product = webwinkel_keuze.product
    aantal = webwinkel_keuze.aantal

    if not product.onbeperkte_voorraad:
        # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
        product.aantal_op_voorraad -= aantal
        product.save(update_fields=['aantal_op_voorraad'])

    prijs = aantal * product.prijs_euro
    return prijs


def webwinkel_plugin_verwijder_reservering(stdout, webwinkel_keuze):
    """
        Deze functie wordt vanuit de achtergrondtaak aangeroepen om een product uit het mandje te halen.
        De reservering wordt ongedaan gemaakt zodat de producten door iemand anders te kiezen zijn.
    """

    product = webwinkel_keuze.product
    aantal = webwinkel_keuze.aantal

    if not product.onbeperkte_voorraad:
        # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
        product.aantal_op_voorraad += aantal
        product.save(update_fields=['aantal_op_voorraad'])

    stdout.write('[INFO] Webwinkel keuze pk=%s wordt verwijderd' % webwinkel_keuze.pk)

    webwinkel_keuze.delete()


def webwinkel_plugin_bepaal_kortingen(stdout, mandje):
    # TODO: kortingen voor de webwinkel
    pass


def webwinkel_plugin_bepaal_verzendkosten_mandje(stdout, mandje):
    """ bereken de verzendkosten voor fysieke producten in het mandje """

    webwinkel_count = 0
    for product in mandje.producten.all():
        if product.webwinkel_keuze:
            webwinkel_count += 1
    # for

    if webwinkel_count > 0:
        # wel verzendkosten
        mandje.verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_VERZENDKOSTEN_EURO)
    else:
        # geen verzendkosten
        mandje.verzendkosten_euro = Decimal(0)

    mandje.save(update_fields=['verzendkosten_euro'])


def webwinkel_plugin_bepaal_verzendkosten_bestelling(stdout, bestelling):
    """ bereken de verzendkosten voor fysieke producten in het mandje """

    webwinkel_count = 0
    for product in bestelling.producten.all():
        if product.webwinkel_keuze:
            webwinkel_count += 1
    # for

    if webwinkel_count > 0:
        # wel verzendkosten
        bestelling.verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_VERZENDKOSTEN_EURO)
    else:
        # geen verzendkosten
        bestelling.verzendkosten_euro = Decimal(0)

    bestelling.save(update_fields=['verzendkosten_euro'])


def webwinkel_beschrijf_product(keuze):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """
    beschrijving = list()

    product = keuze.product

    tup = ('Titel', product.omslag_titel)
    beschrijving.append(tup)

    tup = ('Prijs per stuk', '€ ' + localize(product.prijs_euro))
    beschrijving.append(tup)

    if product.eenheid:
        aantal_enkel, aantal_meer = product.eenheid.split(',')
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


# end of file

