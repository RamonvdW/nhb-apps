# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een beschrijving van een BestellingProduct,
    zodat deze consequent beschreven kunnen worden op het scherm, in e-mails en mogelijk in een pdf.
"""

from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD,
                                   BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_TRANSPORT,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
from Bestelling.models import BestellingRegel
from Bestelling.models.product_obsolete import BestellingProduct
from Bestelling.plugins.evenement import evenement_plugin_beschrijf_product
from Bestelling.plugins.opleiding import opleiding_plugin_beschrijf_product
from Bestelling.plugins.wedstrijden import wedstrijden_plugin_beschrijf_product, wedstrijden_plugin_beschrijf_korting
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

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING:
        wedstrijd_inschrijving = regel.wedstrijdinschrijving_set.first()
        return wedstrijden_plugin_beschrijf_product(wedstrijd_inschrijving)

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD:
        wedstrijd_inschrijving = regel.wedstrijdinschrijving_set.first()        # FUTURE: wedstrijdafgemeld
        return wedstrijden_plugin_beschrijf_product(wedstrijd_inschrijving)

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING:
        # deze moet voor een wedstrijd inschrijving zijn
        wedstrijd_inschrijving = regel.wedstrijdinschrijving_set.first()
        # TODO als de aankoop geannuleerd is, dan hoeven we de korting niet meer te laten zien?
        if wedstrijd_inschrijving:
            kort, redenen = wedstrijden_plugin_beschrijf_korting(wedstrijd_inschrijving.korting)
            redenen.insert(0, kort)
            return redenen

    if regel.code == BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING:
        evenement_inschrijving = regel.evenementinschrijving_set.first()
        return evenement_plugin_beschrijf_product(evenement_inschrijving)

    if regel.code == BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD:
        evenement_afgemeld = regel.evenementafgemeld_set.first()
        return evenement_plugin_beschrijf_product(evenement_afgemeld)

    if regel.code == BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING:
        opleiding_inschrijving = regel.opleidinginschrijving_set.first()
        return opleiding_plugin_beschrijf_product(opleiding_inschrijving)

    if regel.code == BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD:
        opleiding_afgemeld = regel.opleidingafgemeld_set.first()
        return opleiding_plugin_beschrijf_product(opleiding_afgemeld)

    if regel.code == BESTELLING_REGEL_CODE_WEBWINKEL:
        webwinkel_keuze = regel.webwinkelkeuze_set.first()
        return webwinkel_plugin_beschrijf_product(webwinkel_keuze)

    if regel.code == BESTELLING_REGEL_CODE_TRANSPORT:
        # TODO
        pass

    print('HUH? code=%s' % regel.code)
    return []


# end of file
