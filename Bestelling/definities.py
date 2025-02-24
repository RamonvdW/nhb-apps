# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK = 1

BESTELLING_STATUS_NIEUW = 'N'               # producten gereserveerd; betaling nog niet gestart
BESTELLING_STATUS_BETALING_ACTIEF = 'B'     # Mollie opgestart
BESTELLING_STATUS_AFGEROND = 'A'            # 100% betaald; reservering nu definitief
BESTELLING_STATUS_MISLUKT = 'F'             # <100% betaald; wacht op meer
BESTELLING_STATUS_GEANNULEERD = 'G'         # gebruiker wil niet meer; reservering of definitieve plekken vrijgegeven

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
    BESTELLING_STATUS_AFGEROND: 'Voltooid',     # browser vertaalt 'Afgerond' naar 'rounded'
    BESTELLING_STATUS_MISLUKT: 'Mislukt',
    BESTELLING_STATUS_GEANNULEERD: 'Geannuleerd',
}


BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN = 1        # inschrijven op wedstrijd
BESTELLING_MUTATIE_VERWIJDER = 2                    # product verwijderen uit mandje
BESTELLING_MUTATIE_MAAK_BESTELLINGEN = 3            # mandje omzetten in bestelling(en)
BESTELLING_MUTATIE_BETALING_AFGEROND = 4            # betaling is afgerond (gelukt of mislukt)
BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN = 5           # afmelden (na betaling)
BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN = 6        # overboeking ontvangen
BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD = 7        # restitutie uitbetaald
BESTELLING_MUTATIE_WEBWINKEL_KEUZE = 8              # keuze uit webwinkel
BESTELLING_MUTATIE_ANNULEER = 9                     # annuleer een bestelling
BESTELLING_MUTATIE_TRANSPORT = 10                   # wijzig transport keuze
BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN = 11       # inschrijven op evenement
BESTELLING_MUTATIE_EVENEMENT_AFMELDEN = 12          # afmelden (na betaling)
BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN = 13       # inschrijven op opleiding
BESTELLING_MUTATIE_OPLEIDING_AFMELDEN = 14          # afmelden (na betaling)

BESTELLING_MUTATIE_TO_STR = {
    BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN: "Inschrijven op wedstrijd",
    BESTELLING_MUTATIE_WEBWINKEL_KEUZE: "Webwinkel keuze",
    BESTELLING_MUTATIE_VERWIJDER: "Product verwijderen uit mandje",
    BESTELLING_MUTATIE_MAAK_BESTELLINGEN: "Mandje omzetten in bestelling(en)",
    BESTELLING_MUTATIE_BETALING_AFGEROND: "Betaling afgerond",
    BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN: "Afmelden voor wedstrijd",
    BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN: "Overboeking ontvangen",
    BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD: "Restitutie uitbetaald",
    BESTELLING_MUTATIE_ANNULEER: "Annuleer bestelling",
    BESTELLING_MUTATIE_TRANSPORT: "Wijzig transport keuze",
    BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN: "Inschrijven op evenement",
    BESTELLING_MUTATIE_EVENEMENT_AFMELDEN: "Afmelding voor evenement",
    BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN: "Inschrijven op opleiding",
    BESTELLING_MUTATIE_OPLEIDING_AFMELDEN: "Afmelden voor opleiding",
}


BESTELLING_TRANSPORT_NVT = 'N'
BESTELLING_TRANSPORT_VERZEND = 'V'
BESTELLING_TRANSPORT_OPHALEN = 'O'

BESTELLING_TRANSPORT_OPTIES = (
    (BESTELLING_TRANSPORT_NVT, 'Niet van toepassing'),
    (BESTELLING_TRANSPORT_VERZEND, 'Verzend'),
    (BESTELLING_TRANSPORT_OPHALEN, 'Ophalen'),
)

BESTELLING_TRANSPORT2STR = {
    BESTELLING_TRANSPORT_NVT: "Niet van toepassing",
    BESTELLING_TRANSPORT_VERZEND: "Verzend",
    BESTELLING_TRANSPORT_OPHALEN: "Ophalen",
}

# max-length: 10
BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING = "evenement_inschrijving"     # length: 22
BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD = "evenement_afgemeld"
BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING = "opleiding_inschrijving"
BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD = "opleiding_afgemeld"
BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING = "wedstrijd_inschrijving"
BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD = "wedstrijd_afgemeld"
BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING = "wedstrijd_korting"
BESTELLING_REGEL_CODE_WEBWINKEL = "webwinkel"
BESTELLING_REGEL_CODE_TRANSPORT = "transport"


# end of file
