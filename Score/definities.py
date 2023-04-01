# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from decimal import Decimal


AG_NUL = Decimal('0.000')
AG_LAAGSTE_NIET_NUL = Decimal('0.001')

# als een sporter per ongeluk opgenomen is in de uitslag
# dan kan de score aangepast wordt tot SCORE_WAARDE_VERWIJDERD
# om aan te geven dat de sporter eigenlijk toch niet mee deed.
# via scorehist zijn de wijzigingen dan nog in te zien
SCORE_WAARDE_VERWIJDERD = 32767

# gebruik 'geen score' om bij te houden dat gekozen is deze sporterboog te markeren als 'niet geschoten'
# zonder een echt score record aan te maken. Elke sporterboog heeft genoeg aan 1 'geen score' record.
SCORE_TYPE_SCORE = 'S'
SCORE_TYPE_GEEN = 'G'           # niet geschoten

SCORE_CHOICES = (
    (SCORE_TYPE_SCORE, 'Score'),
    (SCORE_TYPE_GEEN, 'Geen score')
)

AG_DOEL_INDIV = 'i'
AG_DOEL_TEAM = 't'

AG_DOEL_CHOICES = (
    (AG_DOEL_INDIV, 'Individueel'),
    (AG_DOEL_TEAM,  'Teamcompetitie')
)


# end of file
