# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert een mapping voor alle bestelling plugins
"""

from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT,
                                   BESTELLING_REGEL_CODE_OPLEIDING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_VERZENDKOSTEN)
from Evenement.plugin_bestelling import evenement_bestel_plugin
from Opleiding.plugin_bestelling import opleiding_bestel_plugin
from Webwinkel.plugin_bestelling import webwinkel_bestel_plugin, verzendkosten_bestel_plugin
from Wedstrijden.plugin_bestelling import wedstrijd_bestel_plugin, wedstrijd_korting_bestel_plugin


bestel_plugins = {
    BESTELLING_REGEL_CODE_EVENEMENT: evenement_bestel_plugin,
    BESTELLING_REGEL_CODE_OPLEIDING: opleiding_bestel_plugin,
    BESTELLING_REGEL_CODE_WEDSTRIJD: wedstrijd_bestel_plugin,
    BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING: wedstrijd_korting_bestel_plugin,
    BESTELLING_REGEL_CODE_WEBWINKEL: webwinkel_bestel_plugin,
    BESTELLING_REGEL_CODE_VERZENDKOSTEN: verzendkosten_bestel_plugin,
}

# end of file
