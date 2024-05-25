# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.db.models.deletion import PROTECT


def maak_speldscores_wa_ster_recurve(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    boog_r = boog_klas.objects.get(afkorting='R')

    spelden = dict()
    for speld in speld_klas.objects.all():
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.all():
        lkls[lkl.volgorde] = lkl
    # for

    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
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
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk = [
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
        ]

        score_klas.objects.bulk_create(bulk)
    # for


def maak_speldscores_wa_ster_compound(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    boog_c = boog_klas.objects.get(afkorting='C')

    spelden = dict()
    for speld in speld_klas.objects.all():
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.all():
        lkls[lkl.volgorde] = lkl
    # for

    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
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
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk = [
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
        ]

        score_klas.objects.bulk_create(bulk)
    # for


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
    for speld in speld_klas.objects.all():
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.all():
        lkls[lkl.volgorde] = lkl
    # for

    # 70m ronde (recurve)
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=550),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=600),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=650),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=675),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=70,
                benodigde_score=700),
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    # 900 ronde
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        for boog in (boog_r, boog_c, boog_bb):
            bulk = [
                score_klas(
                    speld=spelden[3001],        # wit
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=750),
                score_klas(
                    speld=spelden[3002],        # zwart
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=800),
                score_klas(
                    speld=spelden[3003],        # blauw
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=830),
                score_klas(
                    speld=spelden[3004],        # rood
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=860),
                score_klas(
                    speld=spelden[3005],        # goud
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=875),
                score_klas(
                    speld=spelden[3006],        # purper
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    benodigde_score=890),
            ]

            score_klas.objects.bulk_create(bulk)
        # for
    # for

    # 25m ronde
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        for boog in (boog_r, boog_c, boog_bb):
            bulk = [
                score_klas(
                    speld=spelden[3001],        # wit
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=500),
                score_klas(
                    speld=spelden[3002],        # zwart
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=525),
                score_klas(
                    speld=spelden[3003],        # blauw
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=550),
                score_klas(
                    speld=spelden[3004],        # rood
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=575),
                score_klas(
                    speld=spelden[3005],        # goud
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=585),
                score_klas(
                    speld=spelden[3006],        # purper
                    leeftijdsklasse=lkl,
                    boog_type=boog,
                    afstand=25,
                    benodigde_score=595),
            ]

            score_klas.objects.bulk_create(bulk)
        # for
    # for

    # 18m ronde (recurve)
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=525),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=550),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=575),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=585),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=18,
                benodigde_score=595),
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    # 18m ronde (barebow)
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=480),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=500),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=520),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=540),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=550),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=18,
                benodigde_score=560),
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    # 50m ronde (barebow)
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=480),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=500),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=520),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=540),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=550),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_bb,
                afstand=50,
                benodigde_score=560),
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    # 50m ronde (compound)
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3001],        # wit
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=500),
            score_klas(
                speld=spelden[3002],        # zwart
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=550),
            score_klas(
                speld=spelden[3003],        # blauw
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=600),
            score_klas(
                speld=spelden[3004],        # rood
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=650),
            score_klas(
                speld=spelden[3005],        # goud
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=675),
            score_klas(
                speld=spelden[3006],        # purper
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstand=50,
                benodigde_score=700),
        ]

        score_klas.objects.bulk_create(bulk)
    # for

    # 60m ronde (recurve)
    for volgorde in (
            51,     # 50+ dames
            52,     # 50+ heren
            21,     # Onder 18 dames
            22):    # Onder 18 heren

        lkl = lkls[volgorde]

        bulk = [
            score_klas(
                speld=spelden[3101],        # wit, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=500),
            score_klas(
                speld=spelden[3102],        # zwart, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=550),
            score_klas(
                speld=spelden[3103],        # blauw, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=600),
            score_klas(
                speld=spelden[3104],        # rood, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=650),
            score_klas(
                speld=spelden[3105],        # goud, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=675),
            score_klas(
                speld=spelden[3106],        # purper, zilveren
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstand=60,
                benodigde_score=700),
        ]

        score_klas.objects.bulk_create(bulk)
    # for


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
    for speld in speld_klas.objects.all():
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.all():
        lkls[lkl.volgorde] = lkl
    # for

    bulk = [
        score_klas(
            speld=spelden[1001],        # 1000 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1000),
        score_klas(
            speld=spelden[1002],        # 1100 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1100),
        score_klas(
            speld=spelden[1003],        # 1200 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1200),
        score_klas(
            speld=spelden[1004],        # 1300 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1300),
        score_klas(
            speld=spelden[1005],        # 1350 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1350),
        score_klas(
            speld=spelden[1006],        # 1400 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1400),
    ]

    score_klas.objects.bulk_create(bulk)

    krak


def maak_speldscores_nl_tussenspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    boog_r = boog_klas.objects.get(afkorting='R')
    boog_c = boog_klas.objects.get(afkorting='C')
    boog_bb = boog_klas.objects.get(afkorting='BB')

    spelden = dict()
    for speld in speld_klas.objects.all():
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.all():
        lkls[lkl.volgorde] = lkl
    # for

    bulk = [
        score_klas(
            speld=spelden[1001],        # 1000 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1000),
        score_klas(
            speld=spelden[1002],        # 1100 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1100),
        score_klas(
            speld=spelden[1003],        # 1200 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1200),
        score_klas(
            speld=spelden[1004],        # 1300 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1300),
        score_klas(
            speld=spelden[1005],        # 1350 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1350),
        score_klas(
            speld=spelden[1006],        # 1400 ster, recurve
            leeftijdsklasse=None,
            boog_type=boog_r,
            benodigde_score=1400),
    ]

    score_klas.objects.bulk_create(bulk)

    krak


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
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField(default=0)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('boog_type', models.ForeignKey(on_delete=PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=PROTECT, to='BasisTypen.leeftijdsklasse',
                                                      null=True, blank=True)),
                ('speld', models.ForeignKey(on_delete=PROTECT, to='Spelden.speld')),
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
    ]


# end of file
