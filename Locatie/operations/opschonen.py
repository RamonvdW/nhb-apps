# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Locatie.models import Reistijd, WedstrijdLocatie
from Sporter.models import Sporter


def _check_sporter(lat, lon):
    count = Sporter.objects.filter(adres_lat=lat, adres_lon=lon).count()
    return count > 0


def _check_doel(lat, lon):
    count = WedstrijdLocatie.objects.filter(adres_lat=lat, adres_lon=lon).count()
    return count > 0


def _reistijd_verwijder_op_lat_lon(stdout):
    for reistijd in Reistijd.objects.all():
        if not _check_sporter(reistijd.vanaf_lat, reistijd.vanaf_lon):
            stdout.write('[INFO] Verwijder reistijd zonder koppeling met sporter: %s' % reistijd)
            reistijd.delete()

        elif not _check_doel(reistijd.naar_lat, reistijd.naar_lon):
            stdout.write('[INFO] Verwijder reistijd zonder koppeling met wedstrijdlocatie: %s' % reistijd)
            reistijd.delete()
    # for


def reistijd_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen reistijd records die geen koppeling meer hebben met een sporter (=vanaf) of doel (=naar)
    """
    _reistijd_verwijder_op_lat_lon(stdout)


# end of file
