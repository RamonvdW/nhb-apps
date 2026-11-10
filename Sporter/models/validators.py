# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.core.exceptions import ValidationError
import datetime

maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID


def validate_geboorte_datum(datum):
    """ controleer of het geboortejaar redelijk is
        wordt alleen aangeroepen om de input op een formulier te checken
        jaar: Moet tussen 1900 en 5 jaar geleden liggen (jongste lid = 5 jaar)
        raises ValidationError als het jaartal niet goed is
    """
    global maximum_geboortejaar
    if datum.year < 1900 or datum.year > maximum_geboortejaar:
        raise ValidationError(
                'Geboortejaar %(jaar)s is niet valide (min=1900, max=%(max)s)',
                params={'jaar': datum.year,
                        'max': maximum_geboortejaar})


def validate_sinds_datum(datum):
    """ controleer of de sinds_datum redelijk is
        wordt alleen aangeroepen om de input op een formulier te checken
        datum: moet datetime.date() zijn, dus is de combinatie jaar/maand/dag al gecontroleerd
               mag niet in de toekomst liggen
               moet 5 jaar ná het geboortejaar liggen --> geen toegang tot deze info hier
        raises ValidationError als de datum niet goed is
    """
    now = datetime.datetime.now()
    date_now = datetime.date(year=now.year, month=now.month, day=now.day)
    if datum > date_now:
        raise ValidationError('datum van lidmaatschap mag niet in de toekomst liggen')


# end of file
