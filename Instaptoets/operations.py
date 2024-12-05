# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Instaptoets.models import Instaptoets, Vraag, ToetsAntwoord
from django.utils import timezone
import datetime
import random


def selecteer_toets_vragen(toets: Instaptoets):
    todo = 15 - toets.aantal_vragen

    gekozen_pks = list(toets.vraag_antwoord.all().values_list('vraag__pk', flat=True))

    mogelijke_pks = list()
    pk2vraag = dict()   # [pk] = Vraag()
    for vraag in (Vraag.objects.filter(is_actief=True, gebruik_voor_toets=True).exclude(pk__in=gekozen_pks)):
        pk2vraag[vraag.pk] = vraag
        mogelijke_pks.append(vraag.pk)
    # for

    nieuw = list()
    while todo > 0 and len(mogelijke_pks) > 0:
        todo -= 1
        pk = random.choice(mogelijke_pks)
        mogelijke_pks.remove(pk)

        vraag = pk2vraag[pk]
        antwoord = ToetsAntwoord(vraag=vraag, antwoord='?')
        nieuw.append(antwoord)
    # while

    ToetsAntwoord.objects.bulk_create(nieuw)
    toets.vraag_antwoord.set(nieuw)

    toets.aantal_vragen += len(nieuw)
    toets.save()


def selecteer_huidige_vraag(toets: Instaptoets, forceer=False):
    if toets.is_afgerond:
        return

    if toets.huidige_vraag and not forceer:
        if toets.huidige_vraag.antwoord == '?':
            return

    qset = toets.vraag_antwoord.filter(antwoord='?')

    if qset.count() > 0:
        keuze = random.choice(qset)
        toets.huidige_vraag = keuze
        toets.save(update_fields=['huidige_vraag'])


def toets_geldig(toets: Instaptoets):
    """ geef terug of de toets geldig is:
        - moet helemaal gemaakt zijn
        - datum afgerond maximaal 1 jaar geleden

        Returns:
            geldig: True/False
            dagen:  aantal dagen dat de toets nog geldig is
    """
    if toets.aantal_antwoorden >= toets.aantal_vragen:
        verloopt = datetime.date(toets.afgerond.year + 1, toets.afgerond.month, toets.afgerond.day)
        vandaag = timezone.now().date()
        if verloopt > vandaag:
            verschil = (verloopt - vandaag)
            dagen = verschil.days
            return True, dagen

    return False, 0


def controleer_toets(toets: Instaptoets):
    # TODO: implement
    krak


# end of file
