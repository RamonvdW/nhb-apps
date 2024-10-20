# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from decimal import Decimal


def format_bedrag_euro(euros: Decimal):
    """
        Formatteer het bedrag naar een string met een euro prefix en twee decimalen achter de komma.
        Als het bedrag negatief is, zet dan een minteken voor het euro teken

          € 12,34
        - € 12,34
    """
    msg = "€ "

    if euros < 0:
        # zet het min-teken voor het euro teken
        msg = "- " + msg
        euros = 0 - euros

    # we maken ons hier geen zorgen over eventueel afronden
    # dat wordt gedaan bij het opslaan in een DecimalField
    msg += "%.2f" % euros           # provides 12.34
    msg = msg.replace('.', ',')     # Dutch decimal separator

    return msg


# end of file
