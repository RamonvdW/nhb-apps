# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK = 1

BESTELLING_STATUS_NIEUW = 'N'
BESTELLING_STATUS_BETALING_ACTIEF = 'B'
BESTELLING_STATUS_AFGEROND = 'A'
BESTELLING_STATUS_MISLUKT = 'F'
BESTELLING_STATUS_GEANNULEERD = 'G'

BESTELLING_STATUS_CHOICES = (
    (BESTELLING_STATUS_NIEUW, 'Nieuw'),
    (BESTELLING_STATUS_BETALING_ACTIEF, 'Betaling actief'),
    (BESTELLING_STATUS_AFGEROND, 'Afgerond'),
    (BESTELLING_STATUS_MISLUKT, 'Mislukt'),
    (BESTELLING_STATUS_GEANNULEERD, 'Geannuleerd')
)

BESTELLING_STATUS2STR = {
    BESTELLING_STATUS_NIEUW: 'Nieuw',
    BESTELLING_STATUS_BETALING_ACTIEF: 'Betaling actief',
    BESTELLING_STATUS_AFGEROND: 'Voltooid',     # 'Afgerond' vertaalt naar 'rounded'
    BESTELLING_STATUS_MISLUKT: 'Mislukt',
    BESTELLING_STATUS_GEANNULEERD: 'Geannuleerd',
}


BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN = 1        # inschrijven op wedstrijd
BESTEL_MUTATIE_VERWIJDER = 2                    # product verwijderen uit mandje
BESTEL_MUTATIE_MAAK_BESTELLINGEN = 3            # mandje omzetten in bestelling(en)
BESTEL_MUTATIE_BETALING_AFGEROND = 4            # betaling is afgerond (gelukt of mislukt)
BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN = 5           # afmelden (na betaling)
BESTEL_MUTATIE_OVERBOEKING_ONTVANGEN = 6        # overboeking ontvangen
BESTEL_MUTATIE_RESTITUTIE_UITBETAALD = 7        # restitutie uitbetaald
BESTEL_MUTATIE_WEBWINKEL_KEUZE = 8              # keuze uit webwinkel
BESTEL_MUTATIE_ANNULEER = 9                     # annuleer een bestelling
BESTEL_MUTATIE_TRANSPORT = 10                   # wijzig transport keuze
BESTEL_MUTATIE_EVENEMENT_INSCHRIJVEN = 11       # inschrijven op evenement
BESTEL_MUTATIE_EVENEMENT_AFMELDEN = 12          # afmelden (na betaling)

BESTEL_MUTATIE_TO_STR = {
    BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN: "Inschrijven op wedstrijd",
    BESTEL_MUTATIE_WEBWINKEL_KEUZE: "Webwinkel keuze",
    BESTEL_MUTATIE_VERWIJDER: "Product verwijderen uit mandje",
    BESTEL_MUTATIE_MAAK_BESTELLINGEN: "Mandje omzetten in bestelling(en)",
    BESTEL_MUTATIE_BETALING_AFGEROND: "Betaling afgerond",
    BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN: "Afmelden voor wedstrijd",
    BESTEL_MUTATIE_OVERBOEKING_ONTVANGEN: "Overboeking ontvangen",
    BESTEL_MUTATIE_RESTITUTIE_UITBETAALD: "Restitutie uitbetaald",
    BESTEL_MUTATIE_ANNULEER: "Annuleer bestelling",
    BESTEL_MUTATIE_TRANSPORT: "Wijzig transport keuze",
    BESTEL_MUTATIE_EVENEMENT_INSCHRIJVEN: "Inschrijven op evenement",
    BESTEL_MUTATIE_EVENEMENT_AFMELDEN: "Afmelding voor evenement",
}


BESTEL_TRANSPORT_NVT = 'N'
BESTEL_TRANSPORT_VERZEND = 'V'
BESTEL_TRANSPORT_OPHALEN = 'O'

BESTEL_TRANSPORT_OPTIES = (
    (BESTEL_TRANSPORT_NVT, 'Niet van toepassing'),
    (BESTEL_TRANSPORT_VERZEND, 'Verzend'),
    (BESTEL_TRANSPORT_OPHALEN, 'Ophalen'),
)

BESTEL_TRANSPORT2STR = {
    BESTEL_TRANSPORT_NVT: "Niet van toepassing",
    BESTEL_TRANSPORT_VERZEND: "Verzend",
    BESTEL_TRANSPORT_OPHALEN: "Ophalen",
}

# end of file
