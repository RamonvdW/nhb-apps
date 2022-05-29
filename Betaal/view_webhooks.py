# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from Betaal.models import BetaalActief, BETAAL_PAYMENT_ID_MAXLENGTH
from Betaal.mutaties import betaal_mutatieverzoek_payment_status_changed


@csrf_exempt
def simple_view_mollie_webhook(request):
    """ Deze functie wordt aangeroepen om de POST request af te handelen.
        Dit wordt gebruikt als webhook om status changes van Mollie te ontvangen.

        Noteer dat geen csrf-token gebruikt wordt.
    """

    data = request.POST.get('id', '')[:BETAAL_PAYMENT_ID_MAXLENGTH]     # afkappen voor de veiligheid

    # filter rare tekens eruit
    payment_id = ''
    for char in data:
        if char.isalnum() or char == '_':
            payment_id += char
    # for

    # herkennen we deze betaling?
    if BetaalActief.objects.filter(payment_id=payment_id).count() > 0:
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        status = 200
    else:
        # 404 or 403 gives too much content
        # 400 becomes a plain and empty response
        status = 400

    # geef een status 200 terug (binnen 15 seconden) dan stoppen de callbacks
    return HttpResponse(status=status)


# end of file