# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een beschrijving van een BestelProduct,
    zodat deze consequent beschreven kunnen worden op het scherm, in e-mails en mogelijk in een pdf.
"""

from Bestelling.models import BestellingProduct
from Bestelling.plugins.evenement import evenement_plugin_beschrijf_product
from Bestelling.plugins.wedstrijden import wedstrijden_plugin_beschrijf_product, wedstrijden_beschrijf_korting
from Bestelling.plugins.webwinkel import webwinkel_plugin_beschrijf_product


def beschrijf_product(product: BestellingProduct):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan:
        [('Onderwerp', 'Beschrijving'), ...]
    """

    if product.wedstrijd_inschrijving:
        return wedstrijden_plugin_beschrijf_product(product.wedstrijd_inschrijving)

    if product.evenement_inschrijving:
        return evenement_plugin_beschrijf_product(product.evenement_inschrijving)

    if product.evenement_afgemeld:
        return evenement_plugin_beschrijf_product(product.evenement_afgemeld)

    if product.webwinkel_keuze:
        return webwinkel_plugin_beschrijf_product(product.webwinkel_keuze)

    return []


def beschrijf_korting(product):
    """
        Geef de beschrijving van de korting terug:
            korting_str: een tekst string, bijvoorbeeld "Persoonlijke korting"
            korting_redenen: een lijst van redenen (bedoeld om op opeenvolgende regels te tonen)
    """

    if product.wedstrijd_inschrijving:
        return wedstrijden_beschrijf_korting(product.wedstrijd_inschrijving)

    return None, []


# end of file
