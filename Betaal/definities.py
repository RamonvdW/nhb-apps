# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

BETAAL_MUTATIE_START_ONTVANGST = 1
BETAAL_MUTATIE_START_RESTITUTIE = 2
BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED = 3

BETAAL_MUTATIE_TO_STR = {
    BETAAL_MUTATIE_START_ONTVANGST: "Start ontvangst",
    BETAAL_MUTATIE_START_RESTITUTIE: "Start restitutie",
    BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED: "Payment status changed",
}

BETAAL_PAYMENT_ID_MAXLENGTH = 64        # 32 waarschijnlijk genoeg voor Mollie (geen limiet gevonden in docs)
BETAAL_REFUND_ID_MAXLENGTH = 64         # 32 waarschijnlijk genoeg voor Mollie (geen limiet gevonden in docs)
BETAAL_PAYMENT_STATUS_MAXLENGTH = 15
BETAAL_BESCHRIJVING_MAXLENGTH = 100     # aantal taken voor beschrijving op afschrift
MOLLIE_API_KEY_MAXLENGTH = 50           # geen limiet gevonden in docs
BETAAL_KLANT_NAAM_MAXLENGTH = 100
BETAAL_KLANT_ACCOUNT_MAXLENGTH = 100    # standaard: 11 (BIC) + 18 (IBAN), maar flexibel genoeg voor varianten
BETAAL_CHECKOUT_URL_MAXLENGTH = 400

# end of file
