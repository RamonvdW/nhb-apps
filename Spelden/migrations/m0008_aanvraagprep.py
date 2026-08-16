# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.definities import ORGANISATIE_WA
from Spelden.definities import SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR, SPELD_DISCIPLINE_VELD


def maak_voorwaarden_wa_ster_recurve(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_r = boog_klas.objects.get(afkorting='R')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(1001, 1002, 1003, 1004, 1005, 1006, 1201, 1202, 1203, 1204)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA,
                                       volgorde__in=(21, 22, 31, 32, 41, 42, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    soort = "1440-ronde"
    bulk = list()

    # recurve ster
    for volgorde, afstanden in (
            (41, "70, 60, 50, 30"),     # Senioren dames
            (42, "90, 70, 50, 30"),     # Senioren heren
            (31, "70, 60, 50, 30"),     # Onder 21 dames
            (32, "90, 70, 50, 30")):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1001, 1000),       # 1000 ster, recurve
                                    (1002, 1100),       # 1100 ster, recurve
                                    (1003, 1200),       # 1200 ster, recurve
                                    (1004, 1300),       # 1300 ster, recurve
                                    (1005, 1350),       # 1350 ster, recurve
                                    (1006, 1400)]       # 1400 ster, recurve
        ])
    # for

    # recurve zilveren ster
    for volgorde, afstanden in (
            (51, "60, 50, 40, 30"),     # 50+ dames
            (52, "70, 60, 50, 30"),     # 50+ heren
            (21, "60, 50, 40, 30"),     # Onder 18 dames
            (22, "70, 60, 50, 30")):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1201, 1000),       # 1000 zilveren ster, recurve
                                    (1202, 1100),       # 1100 zilveren ster, recurve
                                    (1203, 1200),       # 1200 zilveren ster, recurve
                                    (1204, 1300)]       # 1300 zilveren ster, recurve
        ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_wa_ster_compound(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_c = boog_klas.objects.get(afkorting='C')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(1011, 1012, 1013, 1014, 1015, 1016, 1211, 1212, 1213, 1214)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA, volgorde__in=(21, 22, 31, 32, 41, 42, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    soort = "1440-ronde"
    bulk = list()

    # compound ster
    for volgorde, afstanden in (
            (41, "70, 60, 50, 30"),     # Senioren dames
            (42, "90, 70, 50, 30"),     # Senioren heren
            (31, "70, 60, 50, 30"),     # Onder 21 dames
            (32, "90, 70, 50, 30")):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1011, 1000),       # 1000 zilveren ster, compound
                                    (1012, 1100),       # 1100 zilveren ster, compound
                                    (1013, 1200),       # 1200 zilveren ster, compound
                                    (1014, 1300),       # 1300 zilveren ster, compound
                                    (1015, 1350),       # 1350 zilveren ster, compound
                                    (1016, 1400)]       # 1400 zilveren ster, compound
        ])
    # for

    # compound zilveren ster
    for volgorde, afstanden in (
            (51, "60, 50, 40, 30"),     # 50+ dames
            (52, "70, 60, 50, 30"),     # 50+ heren
            (21, "60, 50, 40, 30"),     # Onder 18 dames
            (22, "70, 60, 50, 30")):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1211, 1000),  # 1000 zilveren ster, compound
                                    (1212, 1100),  # 1100 zilveren ster, compound
                                    (1213, 1200),  # 1200 zilveren ster, compound
                                    (1214, 1300)]  # 1300 zilveren ster, compound
        ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_wa_target_awards(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_r = boog_klas.objects.get(afkorting='R')
    boog_c = boog_klas.objects.get(afkorting='C')
    boog_bb = boog_klas.objects.get(afkorting='BB')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(3001, 3002, 3003, 3004, 3005, 3006,
                                                         3101, 3102, 3103, 3104, 3105, 3106)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA,
                                       volgorde__in=(21, 22, 31, 32, 41, 42, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    bulk = list()

    # 70m ronde (recurve)
    soort = '70m ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[3001],        # wit
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=500),
            voorwaarden_klas(
                speld=spelden[3002],        # zwart
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=550),
            voorwaarden_klas(
                speld=spelden[3003],        # blauw
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=600),
            voorwaarden_klas(
                speld=spelden[3004],        # rood
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=650),
            voorwaarden_klas(
                speld=spelden[3005],        # goud
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=675),
            voorwaarden_klas(
                speld=spelden[3006],        # purper
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="70",
                aantal_pijlen=2*36,
                benodigde_score=700),
        ])
    # for

    # 900 ronde
    soort = '900 ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        for boog in (boog_r, boog_c, boog_bb):
            bulk.extend([
                voorwaarden_klas(
                    speld=spelden[3001],        # wit
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=750),
                voorwaarden_klas(
                    speld=spelden[3002],        # zwart
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=800),
                voorwaarden_klas(
                    speld=spelden[3003],        # blauw
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=830),
                voorwaarden_klas(
                    speld=spelden[3004],        # rood
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=860),
                voorwaarden_klas(
                    speld=spelden[3005],        # goud
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=875),
                voorwaarden_klas(
                    speld=spelden[3006],        # purper
                    discipline=SPELD_DISCIPLINE_OUTDOOR,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstanden="60, 50, 40",
                    aantal_pijlen=3*30,
                    benodigde_score=890),
            ])
        # for
    # for

    # 25m ronde
    soort = '25m ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]
        afstanden = "25"
        aantal_pijlen = 2 * 25

        for discipline in (SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR):
            for boog in (boog_r, boog_c, boog_bb):
                bulk.extend([
                    voorwaarden_klas(
                        speld=spelden[3001],        # wit
                        discipline=discipline,
                        leeftijdsklasse=lkl,
                        wedstrijd_soort=soort,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=500),
                    voorwaarden_klas(
                        speld=spelden[3002],        # zwart
                        discipline=discipline,
                        wedstrijd_soort=soort,
                        leeftijdsklasse=lkl,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=525),
                    voorwaarden_klas(
                        speld=spelden[3003],        # blauw
                        discipline=discipline,
                        leeftijdsklasse=lkl,
                        wedstrijd_soort=soort,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=550),
                    voorwaarden_klas(
                        speld=spelden[3004],        # rood
                        discipline=discipline,
                        leeftijdsklasse=lkl,
                        wedstrijd_soort=soort,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=575),
                    voorwaarden_klas(
                        speld=spelden[3005],        # goud
                        discipline=discipline,
                        leeftijdsklasse=lkl,
                        wedstrijd_soort=soort,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=585),
                    voorwaarden_klas(
                        speld=spelden[3006],        # purper
                        discipline=discipline,
                        leeftijdsklasse=lkl,
                        wedstrijd_soort=soort,
                        boog_type=boog,
                        afstanden=afstanden,
                        aantal_pijlen=aantal_pijlen,
                        benodigde_score=595),
                ])
            # for
        # for
    # for

    # 18m ronde (recurve)
    soort = '18m ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]
        afstanden = "18"
        aantal_pijlen = 2*30

        for discipline in (SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR):
            bulk.extend([
                voorwaarden_klas(
                    speld=spelden[3001],        # wit
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=500),
                voorwaarden_klas(
                    speld=spelden[3002],        # zwart
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=525),
                voorwaarden_klas(
                    speld=spelden[3003],        # blauw
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=550),
                voorwaarden_klas(
                    speld=spelden[3004],        # rood
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=575),
                voorwaarden_klas(
                    speld=spelden[3005],        # goud
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=585),
                voorwaarden_klas(
                    speld=spelden[3006],        # purper
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_r,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=595),
            ])
    # for

    # 18m ronde (barebow)
    soort = '18m ronde (Barebow)'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]
        afstanden = "18"
        aantal_pijlen = 2*30

        for discipline in (SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR):
            bulk.extend([
                voorwaarden_klas(
                    speld=spelden[3001],        # wit
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=480),
                voorwaarden_klas(
                    speld=spelden[3002],        # zwart
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=500),
                voorwaarden_klas(
                    speld=spelden[3003],        # blauw
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=520),
                voorwaarden_klas(
                    speld=spelden[3004],        # rood
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=540),
                voorwaarden_klas(
                    speld=spelden[3005],        # goud
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=550),
                voorwaarden_klas(
                    speld=spelden[3006],        # purper
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_bb,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=560),
            ])
    # for

    # 50m ronde (barebow)
    soort = '50m Barebow ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[3001],        # wit
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=480),
            voorwaarden_klas(
                speld=spelden[3002],        # zwart
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=500),
            voorwaarden_klas(
                speld=spelden[3003],        # blauw
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=520),
            voorwaarden_klas(
                speld=spelden[3004],        # rood
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=540),
            voorwaarden_klas(
                speld=spelden[3005],        # goud
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=550),
            voorwaarden_klas(
                speld=spelden[3006],        # purper
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=560),
        ])
    # for

    # 50m ronde (compound)
    soort = '50m Compound ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[3001],        # wit
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=500),
            voorwaarden_klas(
                speld=spelden[3002],        # zwart
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=550),
            voorwaarden_klas(
                speld=spelden[3003],        # blauw
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=600),
            voorwaarden_klas(
                speld=spelden[3004],        # rood
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=650),
            voorwaarden_klas(
                speld=spelden[3005],        # goud
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=675),
            voorwaarden_klas(
                speld=spelden[3006],        # purper
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden="50",
                aantal_pijlen=2*36,
                benodigde_score=700),
        ])
    # for

    # 60m ronde (recurve)
    soort = '60m ronde'
    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[3101],        # wit, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=500),
            voorwaarden_klas(
                speld=spelden[3102],        # zwart, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=550),
            voorwaarden_klas(
                speld=spelden[3103],        # blauw, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=600),
            voorwaarden_klas(
                speld=spelden[3104],        # rood, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=650),
            voorwaarden_klas(
                speld=spelden[3105],        # goud, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=675),
            voorwaarden_klas(
                speld=spelden[3106],        # purper, zilveren
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden="60",
                aantal_pijlen=2*36,
                benodigde_score=700),
        ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_wa_arrowhead(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_r = boog_klas.objects.get(afkorting='R')
    boog_c = boog_klas.objects.get(afkorting='C')
    boog_bb = boog_klas.objects.get(afkorting='BB')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(2001, 2002, 2003, 2004, 2005)):
        spelden[speld.volgorde] = speld
    # for

    lkl_dames = lkl_klas.objects.get(volgorde=41, organisatie=ORGANISATIE_WA)       # senioren dames
    lkl_heren = lkl_klas.objects.get(volgorde=42, organisatie=ORGANISATIE_WA)       # senioren heren

    soort = 'Arrowhead'
    bulk = [
        # Recurve heren
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=219),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=275),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=309),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=333),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=351),

        # Recurve dames
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=196),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=257),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=293),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=320),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            benodigde_score=340),

        # Compound heren
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=292),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=340),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=367),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=387),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=401),

        # Compound dames
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=275),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=325),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=352),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=373),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            benodigde_score=389),

        # Barebow heren
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=191),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=250),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=287),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=315),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=336),

        # Barebow dames
        voorwaarden_klas(
            speld=spelden[2001],        # Groen
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=182),
        voorwaarden_klas(
            speld=spelden[2002],        # Grijs
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=238),
        voorwaarden_klas(
            speld=spelden[2003],        # Wit
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=272),
        voorwaarden_klas(
            speld=spelden[2004],        # Zwart
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=295),
        voorwaarden_klas(
            speld=spelden[2005],        # Goud
            discipline=SPELD_DISCIPLINE_VELD,
            wedstrijd_soort=soort,
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            benodigde_score=313),
    ]
    voorwaarden_klas.objects.bulk_create(bulk)

    # maak nu de 48-doelen scores: dit is (in 2024) het dubbele van de 24-doelen scores
    bulk = list()
    for obj in voorwaarden_klas.objects.filter(speld__volgorde__in=(2001, 2002, 2003, 2004, 2005)):
        obj.pk = None
        obj.aantal_doelen *= 2
        obj.benodigde_score *= 2
        obj.wedstrijd_soort = 'Dubbele arrowhead'
        bulk.append(obj)
    # for
    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_nl_tussenspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(4001, 4002, 4003, 4004)):
        spelden[speld.volgorde] = speld
    # for

    soort = "1440-ronde"    # was: 'RK Outdoor'
    bulk = [
        voorwaarden_klas(
            speld=spelden[4001],        # tussenspeld wit
            discipline=SPELD_DISCIPLINE_OUTDOOR,
            wedstrijd_soort=soort,
            benodigde_score=950),
        voorwaarden_klas(
            speld=spelden[4002],        # tussenspeld grijs
            discipline=SPELD_DISCIPLINE_OUTDOOR,
            wedstrijd_soort=soort,
            benodigde_score=1050),
        voorwaarden_klas(
            speld=spelden[4003],        # tussenspeld zwart
            discipline=SPELD_DISCIPLINE_OUTDOOR,
            wedstrijd_soort=soort,
            benodigde_score=1150),
        voorwaarden_klas(
            speld=spelden[4004],        # tussenspeld blauw
            discipline=SPELD_DISCIPLINE_OUTDOOR,
            wedstrijd_soort=soort,
            benodigde_score=1250),
    ]

    voorwaarden_klas.objects.bulk_create(bulk)

    krak


def maak_voorwaarden_nl_graadspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(5001, 5002, 5003,
                                                         5101, 5102, 5103,
                                                         5201, 5202, 5203,
                                                         5301, 5302, 5303)):
        spelden[speld.volgorde] = speld
    # for

    lkl_dames = lkl_klas.objects.get(volgorde=41, organisatie=ORGANISATIE_WA)       # senioren dames
    lkl_heren = lkl_klas.objects.get(volgorde=42, organisatie=ORGANISATIE_WA)       # senioren heren

    soort_indoor = 'Indoor'
    soort_outdoor = 'Outdoor'
    soort_veld = 'Veld'
    soort_short_metric = 'Short Metric'

    bulk = [
        # graadspelden Indoor
        voorwaarden_klas(
            speld=spelden[5001],        # Indoor, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=560),
        voorwaarden_klas(
            speld=spelden[5002],        # Indoor, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=520),
        voorwaarden_klas(
            speld=spelden[5003],        # Indoor, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=460),
        voorwaarden_klas(
            speld=spelden[5001],        # Indoor, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=550),
        voorwaarden_klas(
            speld=spelden[5002],        # Indoor, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=510),
        voorwaarden_klas(
            speld=spelden[5003],        # Indoor, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=450),

        # graadspelden Outdoor
        voorwaarden_klas(
            speld=spelden[5101],        # Outdoor, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1250),
        voorwaarden_klas(
            speld=spelden[5102],        # Outdoor, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1150),
        voorwaarden_klas(
            speld=spelden[5103],        # Outdoor, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1025),
        voorwaarden_klas(
            speld=spelden[5101],        # Outdoor, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1225),
        voorwaarden_klas(
            speld=spelden[5102],        # Outdoor, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1125),
        voorwaarden_klas(
            speld=spelden[5103],        # Outdoor, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1000),

        # graadspelden Veld
        voorwaarden_klas(
            speld=spelden[5201],        # Veld, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=300),
        voorwaarden_klas(
            speld=spelden[5202],        # Veld, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=270),
        voorwaarden_klas(
            speld=spelden[5203],        # Veld, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=220),
        voorwaarden_klas(
            speld=spelden[5201],        # Veld, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=260),
        voorwaarden_klas(
            speld=spelden[5202],        # Veld, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=230),
        voorwaarden_klas(
            speld=spelden[5203],        # Veld, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=180),

        # graadspelden Short Metric
        voorwaarden_klas(
            speld=spelden[5301],        # Short Metric, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=635),
        voorwaarden_klas(
            speld=spelden[5302],        # Short Metric, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=585),
        voorwaarden_klas(
            speld=spelden[5303],        # Short Metric, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=510),
        voorwaarden_klas(
            speld=spelden[5301],        # Short Metric, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=610),
        voorwaarden_klas(
            speld=spelden[5302],        # Short Metric, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=560),
        voorwaarden_klas(
            speld=spelden[5303],        # Short Metric, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=500),
    ]
    voorwaarden_klas.objects.bulk_create(bulk)

    krak


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Spelden', 'm0007_nieuwe_spelden'),
        ('Sporter', 'm0033_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='speldaanvraag',
            name='discipline',
            field=models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('VE', 'Veld'), ('XX', 'n.v.t.')],
                                   default='XX', max_length=2),
        ),
        migrations.AlterField(
            model_name='speldaanvraag',
            name='soort_speld',
            field=models.CharField(
                choices=[('Wsr', 'WA ster recurve'), ('Wzsr', 'WA zilveren ster recurve'), ('Wsc', 'WA ster compound'),
                         ('Wzsc', 'WA zilveren ster compound'), ('Wt', 'WA target award'),
                         ('Wtz', 'WA zilveren target award'), ('Wa', 'WA arrowhead speld'),
                         ('Wa24', 'WA arrowhead 2024 speld'), ('Waba', 'WA beginner award'),
                         ('Ngi', 'NL graadspeld indoor'), ('Ngo', 'NL graadspeld outdoor'),
                         ('Ngv', 'NL graadspeld veld'), ('Ngs', 'NL graadspeld short metric'),
                         ('Nga', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')], default='Wsr', max_length=4),
        ),
        migrations.CreateModel(
            name='SpeldVoorwaarden',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('VE', 'Veld'),
                                                         ('XX', 'n.v.t.')],
                                                default='XX',
                                                max_length=2)),
                ('wedstrijd_soort', models.CharField(max_length=20)),
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('afstanden', models.CharField(blank=True, default='', max_length=20)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('aantal_pijlen', models.PositiveSmallIntegerField(default=0)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.leeftijdsklasse')),
                ('speld', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Spelden.speld')),
            ],
            options={
                'verbose_name': 'Speld voorwaarden',
                'verbose_name_plural': 'Speld voorwaarden',
            },
        ),
        migrations.CreateModel(
            name='SpeldAanvraagPrep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt_op', models.DateField(auto_now_add=True)),
                ('heeft_data_stap1', models.BooleanField(default=False)),
                ('heeft_data_stap2', models.BooleanField(default=False)),
                ('heeft_data_stap3', models.BooleanField(default=False)),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('VE', 'Veld'),
                                                         ('XX', 'n.v.t.')],
                                                default='XX', max_length=2)),
                ('boog', models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow')],
                                          default='R', max_length=2)),
                ('score', models.PositiveSmallIntegerField(default=0)),
                ('afstanden', models.CharField(default='', max_length=15)),
                ('aantal_pijlen', models.PositiveSmallIntegerField(default=0)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('voor_sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
                ('wedstrijd_geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')],
                                                        default='M', max_length=1)),
            ],
            options={
                'verbose_name': 'Speld aanvraag prep',
                'verbose_name_plural': 'Speld aanvraag prep',
            },
        ),
        migrations.CreateModel(
            name='SpeldToegekend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('category', models.CharField(max_length=50)),
                ('speld', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Spelden.speld')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Speld Toegekend',
            },
        ),
        migrations.RunPython(maak_voorwaarden_wa_ster_recurve, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_voorwaarden_wa_ster_compound, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_voorwaarden_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_voorwaarden_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        # migrations.RunPython(maak_voorwaarden_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
        # migrations.RunPython(maak_voorwaarden_nl_graadspelden, reverse_code=migrations.RunPython.noop),
    ]

# end of file
