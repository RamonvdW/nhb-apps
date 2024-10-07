# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from Betaal.models import BetaalActief, BETAAL_PAYMENT_ID_MAXLENGTH
from Betaal.mutaties import betaal_mutatieverzoek_payment_status_changed


@csrf_exempt
def simple_view_mollie_webhook(request):
    """ Deze functie wordt aangeroepen om de POST request af te handelen.
        Dit wordt gebruikt als webhook om status changes van Mollie te ontvangen.
    """

    # reageer binnen 15 seconden met status 200, dan stoppen de callbacks

    data = request.POST.get('id', '')[:BETAAL_PAYMENT_ID_MAXLENGTH]     # afkappen voor de veiligheid

    # filter eventuele rare tekens eruit
    payment_id = ''
    for char in data:
        if char.isalnum() or char == '_':
            payment_id += char
    # for

    # TODO: voorkom oneindig aankloppen met hetzelfde payment_id

    # print('[DEBUG] webhook: payment_id=%s' % repr(payment_id))

    # herkennen we deze betaling?
    if BetaalActief.objects.filter(payment_id=payment_id).count() > 0:
        # zet door naar de achtergrond taak, die haalt alle gegevens op bij Mollie
        betaal_mutatieverzoek_payment_status_changed(payment_id)

    # geef altijd status 200 terug, zodat er niets geleerd kan worden (ook advies Mollie)
    return HttpResponse(status=200)


# end of file
