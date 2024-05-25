# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.db.models.deletion import PROTECT
from Spelden.definities import (SPELD_CATEGORIE_WA_STER, SPELD_CATEGORIE_WA_STER_ZILVER,
                                SPELD_CATEGORIE_WA_TARGET_AWARD, SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
                                SPELD_CATEGORIE_WA_ARROWHEAD, SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
                                SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC, SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
                                SPELD_CATEGORIE_NL_TUSSENSPELD)


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
            beschrijving="Groen",
            boog_type=None),
        speld_klas(
            volgorde=2002,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Grijs",
            boog_type=None),
        speld_klas(
            volgorde=2003,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Wit",
            boog_type=None),
        speld_klas(
            volgorde=2004,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=2005,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Goud",
            boog_type=None),
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
            boog_type=None),
        speld_klas(
            volgorde=3002,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=3003,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Blauw",
            boog_type=None),
        speld_klas(
            volgorde=3004,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Rood",
            boog_type=None),
        speld_klas(
            volgorde=3005,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Goud",
            boog_type=None),
        speld_klas(
            volgorde=3006,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Purper",
            boog_type=None),

        # WA zilveren target award
        speld_klas(
            volgorde=3101,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Wit",
            boog_type=None),
        speld_klas(
            volgorde=3102,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=3103,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Blauw",
            boog_type=None),
        speld_klas(
            volgorde=3104,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Rood",
            boog_type=None),
        speld_klas(
            volgorde=3105,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Goud",
            boog_type=None),
        speld_klas(
            volgorde=3106,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Purper",
            boog_type=None),

    ]

    speld_klas.objects.bulk_create(bulk)


def maak_spelden_nl_tussenspelden(apps, _):

    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # NL tussenspelden
        speld_klas(
            volgorde=4001,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="950",
            boog_type=None),
        speld_klas(
            volgorde=4002,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1050",
            boog_type=None),
        speld_klas(
            volgorde=4003,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1150",
            boog_type=None),
        speld_klas(
            volgorde=4004,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1250",
            boog_type=None),
    ]

    speld_klas.objects.bulk_create(bulk)


def maak_spelden_nl_graadspelden(apps, _):
    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # Indoor
        speld_klas(
            volgorde=5001,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="1e graad Indoor",
            boog_type=None),
        speld_klas(
            volgorde=5002,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="2e graad Indoor",
            boog_type=None),
        speld_klas(
            volgorde=5003,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
            beschrijving="1e graad Indoor",
            boog_type=None),

        # Outdoor
        speld_klas(
            volgorde=5101,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="1e graad Outdoor",
            boog_type=None),
        speld_klas(
            volgorde=5102,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="2e graad Outdoor",
            boog_type=None),
        speld_klas(
            volgorde=5103,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
            beschrijving="3e graad Outdoor",
            boog_type=None),

        # Veld
        speld_klas(
            volgorde=5201,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="1e graad Veld",
            boog_type=None),
        speld_klas(
            volgorde=5202,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="2e graad Veld",
            boog_type=None),
        speld_klas(
            volgorde=5203,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
            beschrijving="3e graad Veld",
            boog_type=None),

        # Short Metric
        speld_klas(
            volgorde=5301,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="1e graad Short Metric",
            boog_type=None),
        speld_klas(
            volgorde=5302,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="2e graad Short Metric",
            boog_type=None),
        speld_klas(
            volgorde=5303,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
            beschrijving="3e graad Short Metric",
            boog_type=None),

        # Algemeen
        speld_klas(
            volgorde=5401,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Grootmeesterschutter",        # 1e graad (3 van de 4)
            boog_type=None),
        speld_klas(
            volgorde=5402,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Meesterschutter",             # 2e graad (3 van de 4)
            boog_type=None),
        speld_klas(
            volgorde=5403,
            categorie=SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
            beschrijving="Allroundschutter",            # 3e graad (4 van de 4)
            boog_type=None),
    ]

    speld_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0058_scheids_rk_bk'),
        ('Spelden', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Speld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=30)),
                ('categorie', models.CharField(choices=[('Ws', 'WA ster'), ('Wsz', 'WA zilveren ster'),
                                                        ('Wt', 'WA target award'), ('Wtz', 'WA zilveren target award'),
                                                        ('Wa', 'WA arrowhead speld'), ('Ngi', 'NL graadspeld indoor'),
                                                        ('Ngo', 'NL graadspeld outdoor'), ('Ngv', 'NL graadspeld veld'),
                                                        ('Ngs', 'NL graadspeld short metric'),
                                                        ('Nga', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')],
                                               max_length=3)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=PROTECT, to='BasisTypen.boogtype')),
            ],
            options={
                'verbose_name': 'Speld',
                'verbose_name_plural': 'Spelden',
            },
        ),
        migrations.AlterField(
            model_name='speldaanvraag',
            name='soort_speld',
            field=models.CharField(choices=[('Ws', 'WA ster'), ('Wsz', 'WA zilveren ster'), ('Wt', 'WA target award'),
                                            ('Wtz', 'WA zilveren target award'), ('Wa', 'WA arrowhead speld'),
                                            ('Ngi', 'NL graadspeld indoor'), ('Ngo', 'NL graadspeld outdoor'),
                                            ('Ngv', 'NL graadspeld veld'), ('Ngs', 'NL graadspeld short metric'),
                                            ('Nga', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')],
                                   default='Ws', max_length=3),
        ),
        migrations.RunPython(maak_spelden_wa_ster, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_graadspelden, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
    ]


# end of file
