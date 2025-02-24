# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een beschrijving van een BestellingRegel,
    zodat deze consequent beschreven kunnen worden op het scherm, in e-mails en mogelijk in een pdf.
"""

from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD,
                                   BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_TRANSPORT)
from Bestelling.plugins.alle_bestel_plugins import bestel_plugins
from Bestelling.models import BestellingRegel
from Bestelling.models.product_obsolete import BestellingProduct
from Bestelling.plugins.evenement import evenement_plugin_beschrijf_product
from Bestelling.plugins.opleiding import opleiding_plugin_beschrijf_product
from Bestelling.plugins.wedstrijden import wedstrijden_plugin_beschrijf_product
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

    if product.opleiding_inschrijving:
        return opleiding_plugin_beschrijf_product(product.opleiding_inschrijving)

    if product.opleiding_afgemeld:
        return opleiding_plugin_beschrijf_product(product.opleiding_afgemeld)

    if product.webwinkel_keuze:
        return webwinkel_plugin_beschrijf_product(product.webwinkel_keuze)

    return []


def beschrijf_regel(regel: BestellingRegel):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan:
        [('Onderwerp', 'Beschrijving'), ...]
    """

    obj = None

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING:
        obj = regel.wedstrijdinschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD:
        obj = regel.wedstrijdinschrijving_set.first()        # FUTURE: wedstrijd afgemeld

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING:
        # verwijzing naar de korting staat in de wedstrijdinschrijving
        wedstrijd_inschrijving = regel.wedstrijdinschrijving_set.first()
        if wedstrijd_inschrijving:
            obj = wedstrijd_inschrijving.korting

    if regel.code == BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING:
        obj = regel.evenementinschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD:
        obj = regel.evenementafgemeld_set.first()

    if regel.code == BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING:
        obj = regel.opleidinginschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD:
        obj = regel.opleidingafgemeld_set.first()

    if regel.code == BESTELLING_REGEL_CODE_WEBWINKEL:
        obj = regel.webwinkelkeuze_set.first()

    if regel.code == BESTELLING_REGEL_CODE_TRANSPORT:
        # TODO
        pass

    if obj:
        plugin = bestel_plugins[regel.code]
        return plugin.beschrijf_product(obj)

    print('HUH? code=%s' % regel.code)
    return []


# end of file
