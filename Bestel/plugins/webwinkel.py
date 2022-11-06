# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Webwinkel, zoals kortingen. """


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


# end of file

