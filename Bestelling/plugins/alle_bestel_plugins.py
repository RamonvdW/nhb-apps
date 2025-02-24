# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een mapping voor alle bestelling plugins
"""

from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD,
                                   BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_TRANSPORT)
from Evenement.plugin_bestelling import evenement_bestel_plugin
from Opleiding.plugin_bestelling import opleiding_bestel_plugin
from Webwinkel.plugin_bestelling import webwinkel_bestel_plugin
from Wedstrijden.plugin_bestelling import wedstrijd_bestel_plugin, wedstrijd_korting_bestel_plugin


class TransportHandler(BestelPluginBase):

    def mandje_opschonen(self, verval_datum):
        # nothing to do
        return []

    def beschrijf_product(self, obj) -> list:
        """
            Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
        """
        raise NotImplementedError()


bestel_plugins = {
    BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING: evenement_bestel_plugin,
    BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD: evenement_bestel_plugin,
    BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING: opleiding_bestel_plugin,
    BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD: opleiding_bestel_plugin,
    BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING: wedstrijd_bestel_plugin,
    BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD: wedstrijd_bestel_plugin,
    BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING: wedstrijd_korting_bestel_plugin,
    BESTELLING_REGEL_CODE_WEBWINKEL: webwinkel_bestel_plugin,
    BESTELLING_REGEL_CODE_TRANSPORT: TransportHandler(),
}

# end of file
