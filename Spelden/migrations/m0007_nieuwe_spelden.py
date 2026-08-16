# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Spelden.definities import (SPELD_CATEGORIE_WA_STER_R, SPELD_CATEGORIE_WA_STER_ZILVER_R,
                                SPELD_CATEGORIE_WA_STER_C, SPELD_CATEGORIE_WA_STER_ZILVER_C,
                                SPELD_CATEGORIE_WA_TARGET_AWARD, SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
                                SPELD_CATEGORIE_WA_ARROWHEAD, SPELD_CATEGORIE_WA_ARROWHEAD_2024,
                                SPELD_CATEGORIE_WA_BEGINNER_AWARD,
                                SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_VELD, SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                                SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN, SPELD_CATEGORIE_NL_TUSSENSPELD)


def cleanup_old(apps, _):

    speldscore_klas = apps.get_model('Spelden', 'SpeldScore')
    speldscore_klas.objects.all().delete()

    speld_klas = apps.get_model('Spelden', 'Speld')
    speld_klas.objects.all().delete()


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
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1000",
            pas_code="R1000",
            boog_type=boog_r),
        speld_klas(
            volgorde=1002,
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1100",
            pas_code="R1100",
            boog_type=boog_r),
        speld_klas(
            volgorde=1003,
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1200",
            pas_code="R1200",
            boog_type=boog_r),
        speld_klas(
            volgorde=1004,
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1300",
            pas_code="R1300",
            boog_type=boog_r),
        speld_klas(
            volgorde=1005,
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1350",
            pas_code="R1350",
            boog_type=boog_r),
        speld_klas(
            volgorde=1006,
            categorie=SPELD_CATEGORIE_WA_STER_R,
            beschrijving="1400",
            pas_code="R1400",
            boog_type=boog_r),

        # WA ster, Compound
        speld_klas(
            volgorde=1011,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1000",
            pas_code="C1000",
            boog_type=boog_c),
        speld_klas(
            volgorde=1012,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1100",
            pas_code="C1100",
            boog_type=boog_c),
        speld_klas(
            volgorde=1013,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1200",
            pas_code="C1200",
            boog_type=boog_c),
        speld_klas(
            volgorde=1014,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1300",
            pas_code="C1300",
            boog_type=boog_c),
        speld_klas(
            volgorde=1015,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1350",
            pas_code="C1350",
            boog_type=boog_c),
        speld_klas(
            volgorde=1016,
            categorie=SPELD_CATEGORIE_WA_STER_C,
            beschrijving="1400",
            pas_code="C1400",
            boog_type=boog_c),

        # WA zilveren ster, Recurve
        speld_klas(
            volgorde=1201,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_R,
            beschrijving="Zilveren ster Recurve 1000",
            pas_code="R1000Z",
            boog_type=boog_r),
        speld_klas(
            volgorde=1202,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_R,
            beschrijving="Zilveren ster Recurve 1100",
            pas_code="R1100Z",
            boog_type=boog_r),
        speld_klas(
            volgorde=1203,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_R,
            beschrijving="Zilveren ster Recurve 1200",
            pas_code="R1200Z",
            boog_type=boog_r),
        speld_klas(
            volgorde=1204,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_R,
            beschrijving="Zilveren Ster Recurve 1300",
            pas_code="R1300Z",
            boog_type=boog_r),

        # WA zilveren ster, Compound
        speld_klas(
            volgorde=1211,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_C,
            beschrijving="Zilveren ster Compound 1000",
            pas_code="C1000Z",
            boog_type=boog_c),
        speld_klas(
            volgorde=1212,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_C,
            beschrijving="Zilveren ster Compound 1100",
            pas_code="C1100Z",
            boog_type=boog_c),
        speld_klas(
            volgorde=1213,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_C,
            beschrijving="Zilveren ster Compound 1200",
            pas_code="C1200Z",
            boog_type=boog_c),
        speld_klas(
            volgorde=1214,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER_C,
            beschrijving="Zilveren ster Compound 1300",
            pas_code="C1300Z",
            boog_type=boog_c),
    ]

    speld_klas.objects.bulk_create(bulk)


def maak_spelden_wa_arrowhead(apps, _):

    """
        De arrowhead spelden zien opnieuw gedefinieerd in 2024
        Zie https://extranet.worldarchery.sport/documents/index.php/Rules/Bylaws/English/2023-2025/01_EB_Berlin_26_July_2023/Bylaw_2_-_arrowhead_awards.pdf

    """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    # oude arrowhead spelden (voor 2024)
    bulk = [
        # WA target awards
        speld_klas(
            volgorde=2001,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Groen",
            pas_code="GROEN"),
        speld_klas(
            volgorde=2002,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Bruin",
            pas_code="BRUIN"),
        speld_klas(
            volgorde=2003,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Grijs",
            pas_code="GRIJS"),
        speld_klas(
            volgorde=2004,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Zwart",
            pas_code="ZWART"),
        speld_klas(
            volgorde=2005,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Wit",
            pas_code="WIT"),
        speld_klas(
            volgorde=2006,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Zilver",
            pas_code="ZILVER"),
        speld_klas(
            volgorde=2007,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Goud",
            pas_code="GOUD"),
    ]
    speld_klas.objects.bulk_create(bulk)

    # nieuwe arrowhead spelden (sinds 2024)
    bulk = [
        speld_klas(
            volgorde=2010,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024,
            beschrijving="Groen 24",
            pas_code="GROEN24"),
        speld_klas(
            volgorde=2011,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024,
            beschrijving="Grijs 24",
            pas_code="GRIJS24"),
        speld_klas(
            volgorde=2012,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024,
            beschrijving="Wit 24",
            pas_code="WIT24"),
        speld_klas(
            volgorde=2013,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024,
            beschrijving="Zwart 24",
            pas_code="ZWART24"),
        speld_klas(
            volgorde=2014,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024,
            beschrijving="Goud 24",
            pas_code="GOUD24"),
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
            beschrijving="Wit",
            pas_code="TA-WIT"),
        speld_klas(
            volgorde=3002,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Zwart",
            pas_code="TA-ZWART"),
        speld_klas(
            volgorde=3003,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Blauw",
            pas_code="TA-BLAUW"),
        speld_klas(
            volgorde=3004,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Rood",
            pas_code="TA-ROOD"),
        speld_klas(
            volgorde=3005,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Goud",
            pas_code="TA-GOUD"),
        speld_klas(
            volgorde=3006,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Purper",
            pas_code="TA-PURPER"),

        # WA zilveren target award
        speld_klas(
            volgorde=3101,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Wit",
            pas_code="ZTA-WIT"),
        speld_klas(
            volgorde=3102,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Zwart",
            pas_code="ZTA-ZWART"),
        speld_klas(
            volgorde=3103,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Blauw",
            pas_code="ZTA-BLAUW"),
        speld_klas(
            volgorde=3104,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Rood",
            pas_code="ZTA-ROOD"),
        speld_klas(
            volgorde=3105,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Goud",
            pas_code="ZTA-GOUD"),
        speld_klas(
            volgorde=3106,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zilveren Target Award Purper",
            pas_code="ZTA-PURPER"),
    ]
    speld_klas.objects.bulk_create(bulk)


def maak_spelden_wa_beginner_awards(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # WA beginner awards
        speld_klas(
            volgorde=6001,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Rode Veer",
            pas_code="RVEER"),
        speld_klas(
            volgorde=6002,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Gouden Veer",
            pas_code="GVEER"),
        speld_klas(
            volgorde=6003,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Witte Pijl",
            pas_code="WPIJL"),
        speld_klas(
            volgorde=6004,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Zwarte Pijl",
            pas_code="ZPIJL"),
        speld_klas(
            volgorde=6005,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Blauwe Pijl",
            pas_code="BPIJL"),
        speld_klas(
            volgorde=6006,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Rode Pijl",
            pas_code="RPIJL"),
        speld_klas(
            volgorde=6007,
            categorie=SPELD_CATEGORIE_WA_BEGINNER_AWARD,
            beschrijving="Gouden Pijl",
            pas_code="GPIJL"),
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
            beschrijving="KHSN Tussenspeld 950",    # Wit
            pas_code="TS950",
            prijs_euro=5),
        speld_klas(
            volgorde=4002,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="KHSN Tussenspeld 1050",   # Grijs
            pas_code="TS1050",
            prijs_euro=5),
        speld_klas(
            volgorde=4003,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="KHSN Tussenspeld 1150",   # Zwart
            pas_code="TS1150",
            prijs_euro=5),
        speld_klas(
            volgorde=4004,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="KHSN Tussenspeld 1250",   # Blauw
            pas_code="TS1250",
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
            beschrijving="3e graad Indoor",             # laagste niveau
            pas_code="3GI",
            prijs_euro=5),
        speld_klas(
            volgorde=5002,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="2e graad Indoor",
            pas_code="2GI",
            prijs_euro=5),
        speld_klas(
            volgorde=5003,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="1e graad Indoor",             # hoogste niveau
            pas_code="1GI",
            prijs_euro=5),

        # Outdoor
        speld_klas(
            volgorde=5101,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="3e graad Outdoor",            # laagste niveau
            pas_code="3GO",
            prijs_euro=5),
        speld_klas(
            volgorde=5102,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="2e graad Outdoor",
            pas_code="2GO",
            prijs_euro=5),
        speld_klas(
            volgorde=5103,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="1e graad Outdoor",            # hoogste niveau
            pas_code="1GO",
            prijs_euro=5),

        # Veld
        speld_klas(
            volgorde=5201,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="3e graad Veld",               # laagste niveau
            pas_code="3GV",
            prijs_euro=5),
        speld_klas(
            volgorde=5202,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="2e graad Veld",
            pas_code="2GV",
            prijs_euro=5),
        speld_klas(
            volgorde=5203,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="1e graad Veld",               # hoogste niveau
            pas_code="1GV",
            prijs_euro=5),

        # Short Metric
        speld_klas(
            volgorde=5301,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="3e graad Short Metric",       # laagste niveau
            pas_code="3GSM",
            prijs_euro=5),
        speld_klas(
            volgorde=5302,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="2e graad Short Metric",
            pas_code="2GSM",
            prijs_euro=5),
        speld_klas(
            volgorde=5303,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="1e graad Short Metric",       # hoogste niveau
            pas_code="1GSM",
            prijs_euro=5),

        # Algemeen
        speld_klas(
            volgorde=5401,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Allroundschutter",            # 3e graad (4 van de 4)
            pas_code="AS",
            prijs_euro=5),
        speld_klas(
            volgorde=5402,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Meesterschutter",             # 2e graad (3 van de 4)
            pas_code="MS",
            prijs_euro=5),
        speld_klas(
            volgorde=5403,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Grootmeesterschutter",  # 3 van de 4 spelden 1e graad
            pas_code="GM",
            prijs_euro=5),
    ]
    speld_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0062_squashed'),
        ('Spelden', 'm0006_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Wedstrijden', 'm0063_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='speld',
            name='pas_code',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='speld',
            name='categorie',
            field=models.CharField(
                choices=[('Wsr', 'WA ster recurve'), ('Wzsr', 'WA zilveren ster recurve'), ('Wsc', 'WA ster compound'),
                         ('Wzsc', 'WA zilveren ster compound'), ('Wt', 'WA target award'),
                         ('Wtz', 'WA zilveren target award'), ('Wa', 'WA arrowhead speld'),
                         ('Wa24', 'WA arrowhead 2024 speld'), ('Waba', 'WA beginner award'),
                         ('Ngi', 'NL graadspeld indoor'), ('Ngo', 'NL graadspeld outdoor'),
                         ('Ngv', 'NL graadspeld veld'), ('Ngs', 'NL graadspeld short metric'),
                         ('Nga', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')], max_length=4),
        ),
        migrations.RunPython(cleanup_old, reverse_code=migrations.RunPython.noop),
        migrations.DeleteModel(name='SpeldScore'),
        migrations.RunPython(maak_spelden_wa_ster, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_beginner_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_graadspelden, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
    ]

# end of file
