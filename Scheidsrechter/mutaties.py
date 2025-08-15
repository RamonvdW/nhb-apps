# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Scheidsrechter.definities import (SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN,
                                       SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_WEDSTRIJD,
                                       SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_MATCH,
                                       SCHEIDS_MUTATIE_COMPETITIE_BESCHIKBAARHEID_OPVRAGEN,
                                       SCHEIDS_MUTATIE_REISTIJD_SR_BEPALEN)
from Scheidsrechter.models import ScheidsMutatie
from Site.core.background_sync import BackgroundSync
import datetime
import time


""" Interface naar de achtergrondtaak, waar de mutaties uitgevoerd worden zonder concurrency gevaren """


scheids_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__SCHEIDS_MUTATIES)


def _scheids_ping_achtergrondtaak(mutatie, snel: bool):

    # ping de achtergrondtaak
    scheids_mutaties_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0  # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = ScheidsMutatie.objects.get(pk=mutatie.pk)
        # while


def scheids_mutatieverzoek_beschikbaarheid_opvragen(wedstrijd, door_str, snel: bool):
    """
        Beschikbaarheid van SR opvragen voor specifieke wedstrijd.

        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    recent = timezone.now() - datetime.timedelta(seconds=15)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN,
                                        door=door_str,
                                        wedstrijd=wedstrijd)
    except ScheidsMutatie.objects.MultipleObjectsReturned:      # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


def scheids_mutatieverzoek_stuur_notificaties_wedstrijd(wedstrijd, door_str, snel: bool):
    """
        Eerste keer of wijziging in de gekozen scheidsrechters voor een wedstrijd.
        Achtergrondtaak stuurt een mail naar de wedstrijdleiding en de betroffen scheidsrechters.
    """

    recent = timezone.now() - datetime.timedelta(seconds=15)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_WEDSTRIJD,
                                        door=door_str,
                                        wedstrijd=wedstrijd)
    except ScheidsMutatie.objects.MultipleObjectsReturned:      # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


def scheids_mutatieverzoek_stuur_notificaties_match(match, door_str, snel: bool):
    """
        Eerste keer of wijziging in de gekozen scheidsrechters voor een bondscompetitie wedstrijd.
        Achtergrondtaak stuurt een mail naar de wedstrijdleiding en de betroffen scheidsrechters.
    """

    recent = timezone.now() - datetime.timedelta(seconds=15)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_MATCH,
                                        door=door_str,
                                        match=match)
    except ScheidsMutatie.objects.MultipleObjectsReturned:      # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


def scheids_mutatieverzoek_competitie_beschikbaarheid_opvragen(door_str, snel: bool):
    """
        Beschikbaarheid van SR opvragen voor specifieke wedstrijd.

        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    recent = timezone.now() - datetime.timedelta(seconds=15)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_COMPETITIE_BESCHIKBAARHEID_OPVRAGEN,
                                        door=door_str)
    except ScheidsMutatie.MultipleObjectsReturned:              # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


def scheids_mutatieverzoek_bepaal_reistijd_naar_alle_wedstrijdlocaties(door_str, snel: bool):

    recent = timezone.now() - datetime.timedelta(seconds=15)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_REISTIJD_SR_BEPALEN,
                                        door=door_str)
    except ScheidsMutatie.MultipleObjectsReturned:              # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


# end of file
