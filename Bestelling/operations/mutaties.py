# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Account.models import Account
from Bestelling.definities import (BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTELLING_MUTATIE_WEBWINKEL_KEUZE,
                                   BESTELLING_MUTATIE_MAAK_BESTELLINGEN, BESTELLING_MUTATIE_VERWIJDER,
                                   BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN, BESTELLING_MUTATIE_BETALING_AFGEROND,
                                   BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN, BESTELLING_MUTATIE_ANNULEER,
                                   BESTELLING_MUTATIE_TRANSPORT, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN, BESTELLING_MUTATIE_EVENEMENT_AFMELDEN,
                                   BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN, BESTELLING_MUTATIE_OPLEIDING_AFMELDEN)
from Bestelling.models import BestellingMutatie, Bestelling, BestellingProduct
from Betaal.models import BetaalActief
from Evenement.models import EvenementInschrijving
from Opleiding.models import OpleidingInschrijving
from Site.core.background_sync import BackgroundSync
from Webwinkel.models import WebwinkelKeuze
from Wedstrijden.models import WedstrijdInschrijving
import time


""" Interface naar de achtergrondtaak, waar de mutaties uitgevoerd worden zonder concurrency gevaren """


bestel_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__BESTEL_MUTATIES)


def _bestel_ping_achtergrondtaak(mutatie: BestellingMutatie, snel: bool):

    # ping het achtergrond process
    bestel_mutaties_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0     # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = BestellingMutatie.objects.get(pk=mutatie.pk)
        # while


def bestel_mutatieverzoek_inschrijven_wedstrijd(account: Account, inschrijving: WedstrijdInschrijving, snel: bool):

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN,
                                    account=account,
                                    wedstrijd_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_inschrijven_evenement(account: Account, inschrijving: EvenementInschrijving, snel: bool):

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN,
                                    account=account,
                                    evenement_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_inschrijven_opleiding(account: Account, inschrijving: OpleidingInschrijving, snel: bool):

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN,
                                    account=account,
                                    opleiding_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_webwinkel_keuze(account: Account, keuze: WebwinkelKeuze, snel: bool):

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_WEBWINKEL_KEUZE,
                                    account=account,
                                    webwinkel_keuze=keuze,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_verwijder_product_uit_mandje(account: Account, product: BestellingProduct, snel: bool):
    """
        Verwijder een product uit het mandje

        account: In het mandje van welk account ligt het product nu?
        product: Het product om te verwijderen (inclusief alle kortingen)
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar de achtergrondtaak
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_VERWIJDER,
                                    account=account,
                                    product=product,
                                    is_verwerkt=False)
    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_maak_bestellingen(account: Account, snel=False):
    """
        Zet het mandje om in een bestelling (of meerdere)

        account: Van welk account moeten we het mandje omzetten?
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_MAAK_BESTELLINGEN,
                                    account=account,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving: WedstrijdInschrijving, snel=False):
    """
        Verwijder een inschrijving op een wedstrijd.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN,
                                    wedstrijd_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_afmelden_evenement(inschrijving: EvenementInschrijving, snel=False):
    """
        Verwijder een afmelding voor een evenement.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_EVENEMENT_AFMELDEN,
                                    evenement_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_afmelden_opleiding(inschrijving: OpleidingInschrijving, snel=False):
    """
        Verwijder een afmelding voor een opleiding.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_OPLEIDING_AFMELDEN,
                                    opleiding_inschrijving=inschrijving,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_betaling_afgerond(betaalactief: BetaalActief, gelukt: bool, snel=False):
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
        mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                        code=BESTELLING_MUTATIE_BETALING_AFGEROND,
                                        bestelling=bestelling,
                                        betaling_is_gelukt=gelukt,
                                        is_verwerkt=False)
        if is_created:
            mutatie.save()

            # wacht kort op de achtergrondtaak
            _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_annuleer(bestelling: Bestelling, snel=False):
    """
        Verzoek om een bestelling te annuleren.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_ANNULEER,
                                    bestelling=bestelling,
                                    is_verwerkt=False)
    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_mutatieverzoek_transport(account: Account, transport, snel=False):
    """
        Pad de transport keuze aan

        account: Van welk account moeten we het mandje aanpassen?
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_TRANSPORT,
                                    account=account,
                                    is_verwerkt=False,
                                    transport=transport)
    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


def bestel_betaling_is_gestart(bestelling: Bestelling, actief):
    """ Deze functie wordt aangeroepen vanuit de Betaal daemon om door te geven dat de betaling opgestart
        is en de checkout_url beschikbaar is in dit betaal_actief record
    """
    bestelling.betaal_actief = actief
    bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF

    when_str = timezone.localtime(actief.when).strftime('%Y-%m-%d om %H:%M')

    msg = "\n[%s] Betaling is opgestart (wacht op betaling)" % when_str
    bestelling.log += msg

    bestelling.save(update_fields=['betaal_actief', 'status', 'log'])


def bestel_overboeking_ontvangen(bestelling: Bestelling, bedrag, snel=False):
    """
        Een actieve betaling is afgerond.
    """

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    mutatie, is_created = BestellingMutatie.objects.get_or_create(
                                    code=BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN,
                                    bestelling=bestelling,
                                    bedrag_euro=bedrag,
                                    is_verwerkt=False)

    if is_created:
        mutatie.save()

        # wacht kort op de achtergrondtaak
        _bestel_ping_achtergrondtaak(mutatie, snel)


# end of file
