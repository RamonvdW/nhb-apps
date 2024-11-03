# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.definities import ORGANISATIE_WA
from Spelden.definities import (SPELD_CATEGORIE_WA_STER, SPELD_CATEGORIE_WA_STER_ZILVER,
                                SPELD_CATEGORIE_WA_TARGET_AWARD, SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
                                SPELD_CATEGORIE_WA_ARROWHEAD, SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
                                SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC, SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
                                SPELD_CATEGORIE_NL_TUSSENSPELD)
from decimal import Decimal


def maak_spelden_wa_ster(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_klas.objects.get(afkorting='R')
    boog_c = boog_klas.objects.get(afkorting='C')

    bulk = [
        # WA ster, Recurve
        speld_klas(
            volgorde=1001,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1000",
            boog_type=boog_r),
        speld_klas(
            volgorde=1002,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1100",
            boog_type=boog_r),
        speld_klas(
            volgorde=1003,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1200",
            boog_type=boog_r),
        speld_klas(
            volgorde=1004,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1300",
            boog_type=boog_r),
        speld_klas(
            volgorde=1005,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1350",
            boog_type=boog_r),
        speld_klas(
            volgorde=1006,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1400",
            boog_type=boog_r),

        # WA ster, Compound
        speld_klas(
            volgorde=1011,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1000",
            boog_type=boog_c),
        speld_klas(
            volgorde=1012,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1100",
            boog_type=boog_c),
        speld_klas(
            volgorde=1013,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1200",
            boog_type=boog_c),
        speld_klas(
            volgorde=1014,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1300",
            boog_type=boog_c),
        speld_klas(
            volgorde=1015,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1350",
            boog_type=boog_c),
        speld_klas(
            volgorde=1016,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1400",
            boog_type=boog_c),

        # WA zilveren ster, Recurve
        speld_klas(
            volgorde=1201,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1000",
            boog_type=boog_r),
        speld_klas(
            volgorde=1202,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1100",
            boog_type=boog_r),
        speld_klas(
            volgorde=1203,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1200",
            boog_type=boog_r),
        speld_klas(
            volgorde=1204,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1300",
            boog_type=boog_r),

        # WA zilveren ster, Compound
        speld_klas(
            volgorde=1211,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1000",
            boog_type=boog_c),
        speld_klas(
            volgorde=1212,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1100",
            boog_type=boog_c),
        speld_klas(
            volgorde=1213,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1200",
            boog_type=boog_c),
        speld_klas(
            volgorde=1214,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1300",
            boog_type=boog_c),
    ]

    speld_klas.objects.bulk_create(bulk)


def maak_spelden_wa_arrowhead(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # WA target awards
        speld_klas(
            volgorde=2001,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Groen"),
        speld_klas(
            volgorde=2002,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Grijs"),
        speld_klas(
            volgorde=2003,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Wit"),
        speld_klas(
            volgorde=2004,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Zwart"),
        speld_klas(
            volgorde=2005,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Goud"),
    ]
    speld_klas.objects.bulk_create(bulk)


def maak_spelden_wa_target_awards(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # WA target award
        speld_klas(
            volgorde=3001,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Wit"),
        speld_klas(
            volgorde=3002,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Zwart"),
        speld_klas(
            volgorde=3003,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Blauw"),
        speld_klas(
            volgorde=3004,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Rood"),
        speld_klas(
            volgorde=3005,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Goud"),
        speld_klas(
            volgorde=3006,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Purper"),

        # WA zilveren target award
        speld_klas(
            volgorde=3101,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Wit"),
        speld_klas(
            volgorde=3102,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zwart"),
        speld_klas(
            volgorde=3103,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Blauw"),
        speld_klas(
            volgorde=3104,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Rood"),
        speld_klas(
            volgorde=3105,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Goud"),
        speld_klas(
            volgorde=3106,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Purper"),
    ]
    speld_klas.objects.bulk_create(bulk)


def maak_spelden_nl_tussenspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # NL tussenspelden
        speld_klas(
            volgorde=4001,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="Wit",
            prijs_euro=5),
        speld_klas(
            volgorde=4002,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="Grijs",
            prijs_euro=5),
        speld_klas(
            volgorde=4003,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="Zwart",
            prijs_euro=5),
        speld_klas(
            volgorde=4004,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="Blauw",
            prijs_euro=0),      # TODO: is deze gratis, of geldt "hoogste is gratis, lagere 5,-" per bestelling?
    ]
    speld_klas.objects.bulk_create(bulk)


def maak_spelden_nl_graadspelden(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # Indoor
        speld_klas(
            volgorde=5001,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="1e graad Indoor",
            prijs_euro=5),
        speld_klas(
            volgorde=5002,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="2e graad Indoor",
            prijs_euro=5),
        speld_klas(
            volgorde=5003,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="3e graad Indoor",
            prijs_euro=5),

        # Outdoor
        speld_klas(
            volgorde=5101,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="1e graad Outdoor",
            prijs_euro=5),
        speld_klas(
            volgorde=5102,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="2e graad Outdoor",
            prijs_euro=5),
        speld_klas(
            volgorde=5103,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="3e graad Outdoor",
            prijs_euro=5),

        # Veld
        speld_klas(
            volgorde=5201,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="1e graad Veld",
            prijs_euro=5),
        speld_klas(
            volgorde=5202,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="2e graad Veld",
            prijs_euro=5),
        speld_klas(
            volgorde=5203,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="3e graad Veld",
            prijs_euro=5),

        # Short Metric
        speld_klas(
            volgorde=5301,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="1e graad Short Metric",
            prijs_euro=5),
        speld_klas(
            volgorde=5302,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="2e graad Short Metric",
            prijs_euro=5),
        speld_klas(
            volgorde=5303,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="3e graad Short Metric",
            prijs_euro=5),

        # Algemeen
        speld_klas(
            volgorde=5401,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Grootmeesterschutter",        # 1e graad (3 van de 4)
            prijs_euro=5),
        speld_klas(
            volgorde=5402,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Meesterschutter",             # 2e graad (3 van de 4)
            prijs_euro=5),
        speld_klas(
            volgorde=5403,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Allroundschutter",            # 3e graad (4 van de 4)
            prijs_euro=5),
    ]
    speld_klas.objects.bulk_create(bulk)


def maak_speldscores_wa_ster_recurve(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    score_klas = apps.get_model('Spelden', 'SpeldScore')
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

    replaces = [('Spelden', 'm0001_initial'),
                ('Spelden', 'm0002_spelden'),
                ('Spelden', 'm0003_speldscore'),
                ('Spelden', 'm0004_defaults'),
                ('Spelden', 'm0005_defaults')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0058_scheids_rk_bk'),
        ('Sporter', 'm0031_squashed'),
        ('Wedstrijden', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SpeldAanvraag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt_op', models.DateField(auto_now_add=True)),
                ('last_email_reminder', models.DateTimeField(auto_now_add=True)),
                ('soort_speld', models.CharField(choices=[('Ws', 'WA ster'),
                                                          ('Wsz', 'WA zilveren ster'),
                                                          ('Wt', 'WA target award'),
                                                          ('Wtz', 'WA zilveren target award'),
                                                          ('Wa', 'WA arrowhead speld'),
                                                          ('Ngi', 'NL graadspeld indoor'),
                                                          ('Ngo', 'NL graadspeld outdoor'),
                                                          ('Ngv', 'NL graadspeld veld'),
                                                          ('Ngs', 'NL graadspeld short metric'),
                                                          ('Nga', 'NL graadspeld algemeen'),
                                                          ('Nt', 'NL tussenspeld')],
                                                 default='Ws', max_length=3)),
                ('datum_wedstrijd', models.DateField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'),
                                                         ('IN', 'Indoor'),
                                                         ('VE', 'Veld')],
                                                default='OD', max_length=2)),
                ('log', models.TextField(blank=True, default='')),
                ('boog_type', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('door_account', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('leeftijdsklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.leeftijdsklasse')),
                ('voor_sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Speld aanvraag',
                'verbose_name_plural': 'Speld aanvragen',
            },
        ),
        migrations.CreateModel(
            name='SpeldBijlage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('soort_bijlage', models.CharField(choices=[('s', 'Scorebriefje'),
                                                            ('u', 'Uitslag')],
                                                   default='s', max_length=1)),
                ('bestandstype', models.CharField(choices=[('f', 'Foto'),
                                                           ('p', 'PDF'),
                                                           ('?', '?')],
                                                  default='f', max_length=1)),
                ('log', models.TextField(blank=True, default='')),
                ('aanvraag', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Spelden.speldaanvraag')),
            ],
            options={
                'verbose_name': 'Speld bijlage',
                'verbose_name_plural': 'Speld bijlagen',
            },
        ),
        migrations.CreateModel(
            name='Speld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=30)),
                ('categorie', models.CharField(choices=[('Ws', 'WA ster'),
                                                        ('Wsz', 'WA zilveren ster'),
                                                        ('Wt', 'WA target award'),
                                                        ('Wtz', 'WA zilveren target award'),
                                                        ('Wa', 'WA arrowhead speld'),
                                                        ('Ngi', 'NL graadspeld indoor'),
                                                        ('Ngo', 'NL graadspeld outdoor'),
                                                        ('Ngv', 'NL graadspeld veld'),
                                                        ('Ngs', 'NL graadspeld short metric'),
                                                        ('Nga', 'NL graadspeld algemeen'),
                                                        ('Nt', 'NL tussenspeld')],
                                               max_length=3)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='BasisTypen.boogtype')),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
            ],
            options={
                'verbose_name': 'Speld',
                'verbose_name_plural': 'Spelden',
            },
        ),
        migrations.CreateModel(
            name='SpeldScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wedstrijd_soort', models.CharField(max_length=20)),
                ('speld', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Spelden.speld')),
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField(default=0)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.leeftijdsklasse')),
            ],
            options={
                'verbose_name': 'Speld score',
                'verbose_name_plural': 'Speld scores',
            },
        ),
        migrations.RunPython(maak_spelden_wa_ster, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_graadspelden, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_tussenspelden, reverse_code=migrations.RunPython.noop),

        migrations.RunPython(maak_speldscores_wa_ster_recurve, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_ster_compound, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_speldscores_nl_graadspelden, reverse_code=migrations.RunPython.noop),
    ]

# end of file
