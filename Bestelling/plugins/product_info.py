# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een beschrijving van een BestellingRegel,
    zodat deze consequent beschreven kunnen worden op het scherm, in e-mails en mogelijk in een pdf.
"""

from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT,
                                   BESTELLING_REGEL_CODE_OPLEIDING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_VERZENDKOSTEN)
from Bestelling.plugins.alle_bestel_plugins import bestel_plugins
from Bestelling.models import BestellingRegel


def beschrijf_regel(regel: BestellingRegel):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan:
        [('Onderwerp', 'Beschrijving'), ...]
    """

    obj = None

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD:
        obj = regel.wedstrijdinschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING:
        # verwijzing naar de korting staat in de wedstrijdinschrijving
        wedstrijd_inschrijving = regel.wedstrijdinschrijving_set.first()
        if wedstrijd_inschrijving:
            obj = wedstrijd_inschrijving.korting

    if regel.code == BESTELLING_REGEL_CODE_EVENEMENT:
        obj = regel.evenementinschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_OPLEIDING:
        obj = regel.opleidinginschrijving_set.first()

    if regel.code == BESTELLING_REGEL_CODE_WEBWINKEL:
        obj = regel.webwinkelkeuze_set.first()

    if regel.code == BESTELLING_REGEL_CODE_VERZENDKOSTEN:
        # TODO
        pass

    if obj:
        plugin = bestel_plugins[regel.code]
        return plugin.beschrijf_product(obj)

    print('HUH? code=%s' % regel.code)
    return []


# end of file
