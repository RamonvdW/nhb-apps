# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Bestel.models import (BestelMutatie, Bestelling,
                           BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTEL_MUTATIE_MAAK_BESTELLING,
                           BESTEL_MUTATIE_VERWIJDER, BESTEL_MUTATIE_KORTINGSCODE, BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN,
                           BESTEL_MUTATIE_BETALING_AFGEROND)
from Overig.background_sync import BackgroundSync
import time


""" Interface naar de achtergrondtaak, waar de mutaties uitgevoerd worden zonder concurrency gevaren """


bestel_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__BESTEL_MUTATIES)


def _bestel_ping_achtergrondtaak(mutatie, snel):

    # ping het achtergrond process
    bestel_mutaties_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0  # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = BestelMutatie.objects.get(pk=mutatie.pk)
        # while


def bestel_mutatieverzoek_inschrijven_wedstrijd(account, inschrijving, snel):

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestelMutatie.objects.get_or_create(
                                    code=BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN,
                                    account=account,
                                    inschrijving=inschrijving,
                                    is_verwerkt=False)
    mutatie.save()

    if is_created:                                          # pragma: no branch
        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_verwijder_product_uit_mandje(account, product, snel):
    """
        Verwijder een product uit het mandje

        account: In het mandje van welk account ligt het product nu?
        product: Het product om te verwijderen (inclusief alle kortingen)
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar de achtergrondtaak
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestelMutatie.objects.get_or_create(
                                    code=BESTEL_MUTATIE_VERWIJDER,
                                    account=account,
                                    product=product,
                                    is_verwerkt=False)
    mutatie.save()

    if is_created:
        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_kortingscode_toepassen(account, kortingscode_str, snel):
    """
        Voeg een kortingcode toe aan een mandje.

        account: In het mandje van welk account ligt het product nu?
        code:    De kortingscode tekst
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar de achtergrondtaak
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestelMutatie.objects.get_or_create(
                                    code=BESTEL_MUTATIE_KORTINGSCODE,
                                    account=account,
                                    kortingscode=kortingscode_str,
                                    is_verwerkt=False)

    if is_created:
        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_maak_bestellingen(account, snel=False):
    """
        Zet het mandje om in een bestelling (of meerdere)

        account: Van welk account moeten we het mandje omzetten?
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestelMutatie.objects.get_or_create(
                                    code=BESTEL_MUTATIE_MAAK_BESTELLING,
                                    account=account,
                                    is_verwerkt=False)
    mutatie.save()

    if is_created:
        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=False):
    """
        Verwijder een inschrijving op een wedstrijd.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestelMutatie.objects.get_or_create(
                                    code=BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN,
                                    inschrijving=inschrijving,
                                    is_verwerkt=False)
    mutatie.save()

    if is_created:                                          # pragma: no branch
        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt, snel=False):
    """
        Een actieve betaling is afgerond.
    """

    # zoek de bestelling erbij
    try:
        bestelling = Bestelling.objects.get(betaal_actief=betaalactief)
    except Bestelling.DoesNotExist:
        # bestelling niet kunnen vinden
        pass
    else:
        # zet dit verzoek door naar het mutaties process
        # voorkom duplicates (niet 100%)
        mutatie, is_created = BestelMutatie.objects.get_or_create(
                                        code=BESTEL_MUTATIE_BETALING_AFGEROND,
                                        bestelling=bestelling,
                                        betaling_is_gelukt=gelukt,
                                        is_verwerkt=False)
        mutatie.save()

        if is_created:
            # wacht kort op de achtergrondtaak
            _bestel_ping_achtergrondtaak(mutatie, snel)


# end of file
