# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import BESTELLING_STATUS_BETALING_ACTIEF
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT
from Betaal.models import BetaalActief, BetaalInstellingenVereniging, BetaalTransactie
from Bestelling.operations.mutaties import bestel_mutatieverzoek_betaling_afgerond


def fake_betaling(bestelling: Bestelling, ontvanger: BetaalInstellingenVereniging):
    """
        Simuleer een Mollie betaling

        Let op: caller moet hierna zelf aanroepen: E2EHelpers.verwerk_bestel_mutaties()
    """

    payment_id = 'testje'

    # betaling verwerken
    betaalactief = BetaalActief(
                        ontvanger=ontvanger,
                        payment_id=payment_id,
                        payment_status='paid',
                        log='test')
    betaalactief.save()

    bestelling.betaal_actief = betaalactief
    bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
    bestelling.save(update_fields=['betaal_actief', 'status'])

    BetaalTransactie(
            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
            payment_id=payment_id,
            when=betaalactief.when,
            beschrijving="Test beschrijving",
            bedrag_beschikbaar=bestelling.totaal_euro,
            klant_naam="Pietje Pijlsnel",
            klant_account="1234.5678.9012.3456").save()

    bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)


# end of file
