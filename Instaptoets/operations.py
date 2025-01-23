# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Instaptoets.models import Instaptoets, Vraag, ToetsAntwoord
from Logboek.models import schrijf_in_logboek
from Sporter.models import Sporter
import datetime
import random


def instaptoets_is_beschikbaar():
    return Vraag.objects.count() > 0


def selecteer_toets_vragen(toets: Instaptoets):
    todo = settings.INSTAPTOETS_AANTAL_VRAGEN - toets.aantal_vragen

    gekozen_pks = list(toets.vraag_antwoord.all().values_list('vraag__pk', flat=True))

    mogelijke_pks = dict()      # [categorie.pk] = [vraag.pk, ...]
    pk2vraag = dict()   # [pk] = Vraag()
    for vraag in (Vraag
                  .objects
                  .filter(is_actief=True,
                          gebruik_voor_toets=True)
                  .exclude(pk__in=gekozen_pks)
                  .select_related('categorie')):
        pk2vraag[vraag.pk] = vraag
        if vraag.categorie:
            cat_pk = vraag.categorie.pk
        else:
            cat_pk = -1
        try:
            mogelijke_pks[cat_pk].append(vraag.pk)
        except KeyError:
            mogelijke_pks[cat_pk] = [vraag.pk]
    # for

    nieuw = list()
    cat_pk_done = list()
    skip_count = random.randint(10, 20)     # nodig om niet steeds met de eerste categorie te beginnen
    while todo > 0:
        prev_todo = todo
        for cat_pk, vraag_pks in mogelijke_pks.items():
            if cat_pk not in cat_pk_done:
                cat_pk_done.append(cat_pk)
                if skip_count > 0:
                    skip_count -= 1
                    continue

                if len(vraag_pks) > 0:
                    todo -= 1
                    pk = random.choice(vraag_pks)
                    vraag_pks.remove(pk)
                    vraag = pk2vraag[pk]
                    antwoord = ToetsAntwoord(vraag=vraag, antwoord='?')
                    nieuw.append(antwoord)

            if todo == 0:
                break       # from the for
        # for
        if todo == prev_todo:
            # geen nieuwe vraag meer gevonden
            # laat alle categorieën weer toe
            cat_pk_done = list()
    # while

    ToetsAntwoord.objects.bulk_create(nieuw)
    toets.vraag_antwoord.add(*nieuw)

    toets.aantal_vragen += len(nieuw)
    toets.save()


def selecteer_huidige_vraag(toets: Instaptoets, forceer=False):
    """ selecteer willekeurig een nog niet beantwoorde vraag
    """
    if toets.is_afgerond:
        return

    if toets.huidige_vraag and not forceer:
        if toets.huidige_vraag.antwoord == '?':
            return

    qset = toets.vraag_antwoord.filter(antwoord='?')
    if toets.huidige_vraag:
        qset = qset.exclude(pk=toets.huidige_vraag.pk)

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
    if toets.geslaagd:
        verloopt = datetime.date(toets.afgerond.year + 1, toets.afgerond.month, toets.afgerond.day)
        vandaag = timezone.now().date()
        if verloopt > vandaag:
            verschil = (verloopt - vandaag)
            dagen = verschil.days
            return True, dagen

    return False, 0


def vind_toets(sporter: Sporter) -> Instaptoets | None:
    """ retourneer de meest recente instaptoets van deze sporter """
    toets = (Instaptoets
             .objects
             .filter(sporter=sporter)
             .select_related('huidige_vraag')
             .order_by('-opgestart')            # meest recente toets eerst
             .first())

    return toets


def controleer_toets(toets: Instaptoets):
    toets.aantal_goed = 0
    for antwoord in toets.vraag_antwoord.select_related('vraag').all():
        vraag = antwoord.vraag
        if antwoord.antwoord == vraag.juiste_antwoord:
            toets.aantal_goed += 1
    # for

    # je moet 70% goed hebben
    # corner case: 1/2 = 50% < 70%
    perc_goed = (toets.aantal_goed * 100.0) / toets.aantal_vragen
    toets.geslaagd = perc_goed >= settings.INSTAPTOETS_AANTAL_GOED_EIS
    toets.save(update_fields=['geslaagd', 'aantal_goed'])

    if toets.geslaagd:
        msg = '%s is geslaagd voor de instaptoets' % toets.sporter.lid_nr_en_volledige_naam()
        perc = int((toets.aantal_goed * 100) / toets.aantal_vragen)
        msg += ' (%s van de %s vragen goed = %d%%)' % (toets.aantal_goed, toets.aantal_vragen, perc)

        schrijf_in_logboek(toets.sporter.account, 'Instaptoets', msg)


# end of file
