# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Functie.models import Functie


def maak_functie(beschrijving, rol):
    """ Deze helper geeft het Functie-object terug met de gevraagde parameters
        De eerste keer wordt deze aangemaakt.
    """
    functie, _ = Functie.objects.get_or_create(beschrijving=beschrijving, rol=rol)
    return functie      # caller kan zelf andere velden invullen


# end of file
