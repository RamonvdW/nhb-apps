# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction, IntegrityError
from django.db.models import ProtectedError
from BasisTypen.definities import GESLACHT_ANDERS
from BasisTypen.models import BoogType
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren


def get_sporter_gekozen_bogen(sporter: Sporter, alle_bogen) -> tuple[dict[str, SporterBoog], list[str]]:
    """ geeft een dictionary terug met een mapping van boog afkorting naar SporterBoog
        geeft een lijst terug met boog afkortingen waarmee wedstrijden geschoten willen worden
    """
    # stel vast welke boogtypen de sporter mee wil schieten (opt-in)
    boog_dict = dict()      # [afkorting] = BoogType()
    for boogtype in alle_bogen:
        boog_dict[boogtype.afkorting] = boogtype
    # for

    boog_afkorting_wedstrijd = list()
    boogafk2sporterboog = dict()       # [boog_afkorting] = SporterBoog()
    # typische 0 tot 20 records (5 WA + vele IFAA)
    for sporterboog in (sporter
                        .sporterboog_set
                        .filter(boogtype__in=alle_bogen)
                        .select_related('boogtype')
                        .order_by('boogtype__volgorde')):
        if sporterboog.voor_wedstrijd:
            afkorting = sporterboog.boogtype.afkorting
            boog_afkorting_wedstrijd.append(afkorting)
            boogafk2sporterboog[afkorting] = sporterboog
    # for

    return boogafk2sporterboog, boog_afkorting_wedstrijd


def get_sporter_voorkeuren(sporter: Sporter, mag_database_wijzigen=False) -> SporterVoorkeuren:
    """ zoek het SporterVoorkeuren object erbij, of maak een nieuwe aan
    """

    if mag_database_wijzigen:
        voorkeuren, was_created = SporterVoorkeuren.objects.get_or_create(sporter=sporter)
    else:
        try:
            voorkeuren = SporterVoorkeuren.objects.get(sporter=sporter)
            was_created = False
        except SporterVoorkeuren.DoesNotExist:
            voorkeuren = SporterVoorkeuren(sporter=sporter)
            was_created = True

    if was_created:
        updated = list()

        # default voor wedstrijd_geslacht_gekozen = True
        if sporter.geslacht != GESLACHT_ANDERS:
            if sporter.geslacht != voorkeuren.wedstrijd_geslacht:  # default is Man
                voorkeuren.wedstrijd_geslacht = sporter.geslacht
                updated.append('wedstrijd_geslacht')
        else:
            voorkeuren.wedstrijd_geslacht_gekozen = False  # laat de sporter kiezen
            updated.append('wedstrijd_geslacht_gekozen')

        if mag_database_wijzigen and len(updated):
            voorkeuren.save(update_fields=updated)

    return voorkeuren


def get_sporter_voorkeuren_wedstrijdbogen(lid_nr):
    """ retourneer de sporter, voorkeuren en pk's van de boogtypen geselecteerd voor wedstrijden """
    pks = list()
    sporter = None
    voorkeuren = None
    try:
        sporter = (Sporter
                   .objects
                   .prefetch_related('sportervoorkeuren_set')
                   .get(lid_nr=lid_nr))
    except (ValueError, Sporter.DoesNotExist):
        pass
    else:
        voorkeuren = get_sporter_voorkeuren(sporter)

        for sporterboog in (SporterBoog
                            .objects
                            .select_related('boogtype')
                            .filter(sporter__lid_nr=lid_nr,
                                    voor_wedstrijd=True)):
            pks.append(sporterboog.boogtype.id)
        # for

    return sporter, voorkeuren, pks


def get_sporterboog(sporter, mag_database_wijzigen=False, geen_wedstrijden=False):

    if geen_wedstrijden:
        # sporter mag niet aan wedstrijden deelnemen
        # verwijder daarom alle SporterBoog records
        if mag_database_wijzigen:
            # er zijn een aantal referentie met on_delete=models.PROTECT dus hanteer fouten
            with transaction.atomic():
                try:
                    SporterBoog.objects.filter(sporter=sporter).delete()
                except ProtectedError:
                    pass

        return list()

    else:
        # maak ontbrekende SporterBoog records aan, indien nodig
        # TODO: aantal bogen globaal opslaan?
        boogtypen = BoogType.objects.exclude(buiten_gebruik=True)       # wordt pas uitgevoerd door len() hieronder

        # haal de SporterBoog records op van deze gebruiker
        objs = (SporterBoog
                .objects
                .filter(sporter=sporter)
                .select_related('boogtype',
                                'sporter')
                .order_by('boogtype__volgorde'))

        if len(objs) < len(boogtypen):
            # er ontbreken een aantal SporterBoog
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            bulk = list()
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                sporterboog = SporterBoog(
                                    sporter=sporter,
                                    boogtype=boogtype)
                bulk.append(sporterboog)
            # for

            if mag_database_wijzigen:
                with transaction.atomic():
                    try:
                        SporterBoog.objects.bulk_create(bulk)
                    except IntegrityError:                                          # pragma: no cover
                        # omdat SporterBoog een unique_together constraint heeft
                        # kunnen we hier komen als concurrency optreedt
                        pass

                objs = (SporterBoog
                        .objects
                        .filter(sporter=sporter)
                        .select_related('boogtype',
                                        'sporter')
                        .order_by('boogtype__volgorde'))
            else:
                bulk.extend(list(objs))
                objs = bulk

        return objs


# end of file
