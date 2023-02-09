# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Competitie
from Competitie.operations import (competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand,
                                   competitie_klassengrenzen_vaststellen)


def maak_competities_en_zet_fase_c(startjaar=None):
    """ Competities 18m en 25m aanmaken, AG vaststellen, klassengrenzen vaststelen, instellen op fase C
        zodat er ingeschreven kan worden.
    """

    # dit voorkomt kennis en afhandelen van achtergrondtaken in alle applicatie test suites

    # competitie aanmaken
    competities_aanmaken(startjaar)

    comp_18 = Competitie.objects.get(afstand='18')
    comp_25 = Competitie.objects.get(afstand='25')

    # aanvangsgemiddelden vaststellen
    aanvangsgemiddelden_vaststellen_voor_afstand(18)
    aanvangsgemiddelden_vaststellen_voor_afstand(25)

    # klassengrenzen vaststellen
    competitie_klassengrenzen_vaststellen(comp_18)
    competitie_klassengrenzen_vaststellen(comp_25)

    zet_competitie_fases(comp_18, 'C', 'C')
    zet_competitie_fases(comp_25, 'C', 'C')

    return comp_18, comp_25


# end of file
