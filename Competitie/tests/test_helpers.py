# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Competitie
from Competitie.operations import (competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand,
                                   competitie_klassengrenzen_vaststellen)
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven


def maak_competities_en_zet_fase_c(startjaar=None):
    """ Competities 18m en 25m aanmaken, AG vaststellen, klassengrenzen vaststelen, instellen op fase C
        zodat er ingeschreven kan worden.
    """

    # dit voorkomt kennis en afhandelen van achtergrondtaken in alle applicatie test suites

    # competitie aanmaken
    competities_aanmaken(startjaar)

    qset = Competitie.objects.all().order_by('begin_jaar')
    if startjaar:
        qset = qset.filter(begin_jaar=startjaar)

    comp_18 = qset.filter(afstand='18').first()
    comp_25 = qset.filter(afstand='25').first()

    # aanvangsgemiddelden vaststellen
    aanvangsgemiddelden_vaststellen_voor_afstand(18)
    aanvangsgemiddelden_vaststellen_voor_afstand(25)

    # klassengrenzen vaststellen
    competitie_klassengrenzen_vaststellen(comp_18)
    competitie_klassengrenzen_vaststellen(comp_25)

    zet_competitie_fase_regio_inschrijven(comp_18)
    zet_competitie_fase_regio_inschrijven(comp_25)

    return comp_18, comp_25


# end of file
