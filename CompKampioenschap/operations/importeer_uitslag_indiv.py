# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Kampioenschap, CompetitieIndivKlasse, KampioenschapSporterBoog
from CompKampioenschap.models import SheetStatus


def importeert_sheet_uitslag_indiv(deelkamp: Kampioenschap, klasse: CompetitieIndivKlasse, status: SheetStatus) -> list[str]:
    """ Lees de uitslag uit een Google Sheet en sla deze op in de database """
    fouten = list()

    regels = ['dit is een test', 'nog een regel']
    fouten.append(regels)
    fouten.append(regels)
    fouten.append(regels)

    return fouten


# end of file
