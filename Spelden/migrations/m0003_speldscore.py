# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.db.models.deletion import PROTECT
from BasisTypen.definities import ORGANISATIE_KHSN, ORGANISATIE_WA


def maak_speldscores_wa_ster_recurve(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

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

    bulk = list()
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            # recurve ster
            score_klas(
                speld=spelden[1001],        # 1000 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1000),
            score_klas(
                speld=spelden[1002],        # 1100 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1100),
            score_klas(
                speld=spelden[1003],        # 1200 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1200),
            score_klas(
                speld=spelden[1004],        # 1300 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1300),
            score_klas(
                speld=spelden[1005],        # 1350 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1350),
            score_klas(
                speld=spelden[1006],        # 1400 ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1400),
        ])
    # for

    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            # recurve ster
            score_klas(
                speld=spelden[1201],        # 1000 zilveren ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1000),
            score_klas(
                speld=spelden[1202],        # 1100 zilveren ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1100),
            score_klas(
                speld=spelden[1203],        # 1200 zilveren ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1200),
            score_klas(
                speld=spelden[1204],        # 1300 zilveren ster, recurve
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                benodigde_score=1300),
        ])
    # for

    score_klas.objects.bulk_create(bulk)


def maak_speldscores_wa_ster_compound(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    boog_c = boog_klas.objects.get(afkorting='C')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(1011, 1012, 1013, 1014, 1015, 1016, 1211, 1212, 1213, 1214)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA, volgorde__in=(21, 22, 31, 32, 41, 42, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    bulk = list()
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk.extend([
            # compound ster
            score_klas(
                speld=spelden[1011],        # 1000 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1000),
            score_klas(
                speld=spelden[1012],        # 1100 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1100),
            score_klas(
                speld=spelden[1013],        # 1200 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1200),
            score_klas(
                speld=spelden[1014],        # 1300 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1300),
            score_klas(
                speld=spelden[1015],        # 1350 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1350),
            score_klas(
                speld=spelden[1016],        # 1400 ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1400),
        ])
    # for

    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            # compound ster
            score_klas(
                speld=spelden[1211],        # 1000 zilveren ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1000),
            score_klas(
                speld=spelden[1212],        # 1100 zilveren ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1100),
            score_klas(
                speld=spelden[1213],        # 1200 zilveren ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1200),
            score_klas(
                speld=spelden[1214],        # 1300 zilveren ster, compound
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                benodigde_score=1300),
        ])
    # for

    score_klas.objects.bulk_create(bulk)


def maak_speldscores_wa_target_awards(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

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
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
                benodigde_score=600),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
                benodigde_score=650),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
                benodigde_score=675),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                wedstrijd_soort=soort,
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
                score_klas(
                    speld=spelden[3001],        # wit
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
                    benodigde_score=750),
                score_klas(
                    speld=spelden[3002],        # zwart
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
                    benodigde_score=800),
                score_klas(
                    speld=spelden[3003],        # blauw
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
                    benodigde_score=830),
                score_klas(
                    speld=spelden[3004],        # rood
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
                    benodigde_score=860),
                score_klas(
                    speld=spelden[3005],        # goud
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
                    benodigde_score=875),
                score_klas(
                    speld=spelden[3006],        # purper
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    wedstrijd_soort=soort,
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

        for boog in (boog_r, boog_c, boog_bb):
            bulk.extend([
                score_klas(
                    speld=spelden[3001],        # wit
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=500),
                score_klas(
                    speld=spelden[3002],        # zwart
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=525),
                score_klas(
                    speld=spelden[3003],        # blauw
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=550),
                score_klas(
                    speld=spelden[3004],        # rood
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=575),
                score_klas(
                    speld=spelden[3005],        # goud
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=585),
                score_klas(
                    speld=spelden[3006],        # purper
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    wedstrijd_soort=soort,
                    benodigde_score=595),
            ])
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

        bulk.extend([
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=525),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=575),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=585),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                wedstrijd_soort=soort,
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

        bulk.extend([
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=480),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=520),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=540),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                wedstrijd_soort=soort,
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
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=480),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=520),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=540),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                wedstrijd_soort=soort,
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
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=600),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=650),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
                benodigde_score=675),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                wedstrijd_soort=soort,
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
            score_klas(
                speld=spelden[3101],        # wit, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=500),
            score_klas(
                speld=spelden[3102],        # zwart, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=550),
            score_klas(
                speld=spelden[3103],        # blauw, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=600),
            score_klas(
                speld=spelden[3104],        # rood, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=650),
            score_klas(
                speld=spelden[3105],        # goud, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=675),
            score_klas(
                speld=spelden[3106],        # purper, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                wedstrijd_soort=soort,
                benodigde_score=700),
        ])
    # for

    score_klas.objects.bulk_create(bulk)


def maak_speldscores_wa_arrowhead(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

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
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=219),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=275),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=309),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=333),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_heren,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=351),

        # Recurve dames
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=196),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=257),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=293),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=320),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_dames,
            boog_type=boog_r,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=340),

        # Compound heren
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=292),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=340),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=367),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=387),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_heren,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=401),

        # Compound dames
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=275),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=325),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=352),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=373),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_dames,
            boog_type=boog_c,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=389),

        # Barebow heren
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=191),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=250),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=287),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=315),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_heren,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=336),

        # Barebow dames
        score_klas(
            speld=spelden[2001],        # Groen
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=182),
        score_klas(
            speld=spelden[2002],        # Grijs
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=238),
        score_klas(
            speld=spelden[2003],        # Wit
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=272),
        score_klas(
            speld=spelden[2004],        # Zwart
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=295),
        score_klas(
            speld=spelden[2005],        # Goud
            leeftijdsklasse=lkl_dames,
            boog_type=boog_bb,
            aantal_doelen=24,
            wedstrijd_soort=soort,
            benodigde_score=313),
    ]
    score_klas.objects.bulk_create(bulk)

    # maak nu de 48-doelen scores: dit is (in 2024) het dubbele van de 24-doelen scores
    bulk = list()
    for obj in score_klas.objects.filter(speld__volgorde__in=(2001, 2002, 2003, 2004, 2005)):
        obj.pk = None
        obj.aantal_doelen *= 2
        obj.benodigde_score *= 2
        obj.wedstrijd_soort = 'Dubbele arrowhead'
        bulk.append(obj)
    # for
    score_klas.objects.bulk_create(bulk)


def maak_speldscores_nl_tussenspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(4001, 4002, 4003, 4004)):
        spelden[speld.volgorde] = speld
    # for

    soort = 'RK Outdoor'
    bulk = [
        score_klas(
            speld=spelden[4001],        # tussenspeld wit
            wedstrijd_soort=soort,
            benodigde_score=950),
        score_klas(
            speld=spelden[4002],        # tussenspeld grijs
            wedstrijd_soort=soort,
            benodigde_score=1050),
        score_klas(
            speld=spelden[4003],        # tussenspeld zwart
            wedstrijd_soort=soort,
            benodigde_score=1150),
        score_klas(
            speld=spelden[4004],        # tussenspeld blauw
            wedstrijd_soort=soort,
            benodigde_score=1250),
    ]

    score_klas.objects.bulk_create(bulk)


def maak_speldscores_nl_graadspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

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
        score_klas(
            speld=spelden[5001],        # Indoor, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=560),
        score_klas(
            speld=spelden[5002],        # Indoor, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=520),
        score_klas(
            speld=spelden[5003],        # Indoor, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_indoor,
            benodigde_score=460),
        score_klas(
            speld=spelden[5001],        # Indoor, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=550),
        score_klas(
            speld=spelden[5002],        # Indoor, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=510),
        score_klas(
            speld=spelden[5003],        # Indoor, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_indoor,
            benodigde_score=450),

        # graadspelden Outdoor
        score_klas(
            speld=spelden[5101],        # Outdoor, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1250),
        score_klas(
            speld=spelden[5102],        # Outdoor, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1150),
        score_klas(
            speld=spelden[5103],        # Outdoor, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1025),
        score_klas(
            speld=spelden[5101],        # Outdoor, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1225),
        score_klas(
            speld=spelden[5102],        # Outdoor, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1125),
        score_klas(
            speld=spelden[5103],        # Outdoor, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_outdoor,
            benodigde_score=1000),

        # graadspelden Veld
        score_klas(
            speld=spelden[5201],        # Veld, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=300),
        score_klas(
            speld=spelden[5202],        # Veld, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=270),
        score_klas(
            speld=spelden[5203],        # Veld, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_veld,
            benodigde_score=220),
        score_klas(
            speld=spelden[5201],        # Veld, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=260),
        score_klas(
            speld=spelden[5202],        # Veld, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=230),
        score_klas(
            speld=spelden[5203],        # Veld, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_veld,
            benodigde_score=180),

        # graadspelden Short Metric
        score_klas(
            speld=spelden[5301],        # Short Metric, 1e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=635),
        score_klas(
            speld=spelden[5302],        # Short Metric, 2e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=585),
        score_klas(
            speld=spelden[5303],        # Short Metric, 3e graad
            leeftijdsklasse=lkl_heren,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=510),
        score_klas(
            speld=spelden[5301],        # Short Metric, 1e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=610),
        score_klas(
            speld=spelden[5302],        # Short Metric, 2e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=560),
        score_klas(
            speld=spelden[5303],        # Short Metric, 3e graad
            leeftijdsklasse=lkl_dames,
            wedstrijd_soort=soort_short_metric,
            benodigde_score=500),
    ]
    score_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0058_scheids_rk_bk'),
        ('Spelden', 'm0002_spelden'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SpeldScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wedstrijd_soort', models.CharField(max_length=20)),
                ('speld', models.ForeignKey(on_delete=PROTECT, to='Spelden.speld')),
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField(default=0)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=PROTECT, to='BasisTypen.leeftijdsklasse',
                                                      null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Speld score',
                'verbose_name_plural': 'Speld scores',
            },
        ),
        migrations.RunPython(maak_speldscores_wa_ster_recurve, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_ster_compound, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_nl_graadspelden, reverse_code=migrations.RunPython.noop),
    ]


# end of file
