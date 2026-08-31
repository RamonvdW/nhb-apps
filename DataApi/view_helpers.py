# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
import datetime


def datum_n_jaar_geleden(jaren: int) -> str:
    now = datetime.datetime.now()

    dagen = jaren * 365
    dagen += jaren // 4     # schrikkeljaren hebben 1 dag meer

    now -= datetime.timedelta(days=dagen)
    return now.strftime('%Y-%m-%d')


def is_auth_token_ok(request):
    """ Controleer dat de HTTP header "DDI-Token" aanwezig is met de juiste waarde
        Django geeft deze door in request.META als HTTP_DDI_TOKEN
    """

    if settings.DDI_AUTH_TOKEN:
        # is configured for DDI
        token_value = request.META.get('HTTP_DDI_TOKEN', None)
        if token_value:
            # header is aanwezig
            token_value = str(token_value)[:64]             # afkappen voor de veiligheid
            if token_value == settings.DDI_AUTH_TOKEN:
                # inhoud klopt ook
                return True

    return False


# end of file
