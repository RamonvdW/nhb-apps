# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from DataApi.models import DataApiLidmaatschap
import datetime


def dataapi_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        we verwijderen lidmaatschappen die meer dan 5 jaar geleden afgemeld zijn
    """

    jaren = 5
    dagen = jaren * 365
    dagen += jaren // 4  # schrikkeljaren hebben 1 dag meer

    vijf_jaar_geleden = datetime.datetime.now() - datetime.timedelta(days=dagen)
    vijf_jaar_geleden = vijf_jaar_geleden.strftime('%Y-%m-%d')

    qset = DataApiLidmaatschap.objects.filter(afmeld_datum__lte=vijf_jaar_geleden)

    stdout.write('[DEBUG] DataApi zou %s lidmaatschappen op kunnen schonen' % qset.count())


# end of file
