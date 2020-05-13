# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from djangosaml2idp.processors import BaseProcessor
from .rol import rol_mag_wisselen


class WikiAccessCheck(BaseProcessor):

    """ Deze processor hoort bij de SAML2 Identity Provider
        Implementatie bepaalt of de gebruiker toegang heeft tot de wiki
        Referentie vanuit settings.py, SAML_IDP_SPCONFIG
    """

    def has_access(self, request):
        """ Deze methode moet bepalen of de gebruiker in de wiki mag
            Resultaat:
                True  = wel  toegang tot wiki geven
                False = geen toegang tot wiki geven
        """
        # als de gebruiker van rol mag wisselen
        # dan is de wiki ook toegestaan
        return rol_mag_wisselen(request)

# end of file
