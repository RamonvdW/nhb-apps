# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.db.models.deletion import PROTECT
from Spelden.definities import (SPELD_CATEGORIE_WA_STER, SPELD_CATEGORIE_WA_STER_ZILVER,
                                SPELD_CATEGORIE_WA_TARGET_AWARD, SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
                                SPELD_CATEGORIE_WA_ARROWHEAD,
                                SPELD_CATEGORIE_NL_GRAADSPELD, SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
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
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1000",
            boog_type=boog_r),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1100",
            boog_type=boog_r),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1200",
            boog_type=boog_r),
        speld_klas(
            volgorde=4,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1300",
            boog_type=boog_r),
        speld_klas(
            volgorde=5,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1350",
            boog_type=boog_r),
        speld_klas(
            volgorde=6,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1400",
            boog_type=boog_r),

        # WA ster, Compound
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1000",
            boog_type=boog_c),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1100",
            boog_type=boog_c),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1200",
            boog_type=boog_c),
        speld_klas(
            volgorde=4,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1300",
            boog_type=boog_c),
        speld_klas(
            volgorde=5,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1350",
            boog_type=boog_c),
        speld_klas(
            volgorde=6,
            categorie=SPELD_CATEGORIE_WA_STER,
            beschrijving="1400",
            boog_type=boog_c),

        # WA zilveren ster, Recurve
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1000",
            boog_type=boog_r),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1100",
            boog_type=boog_r),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1200",
            boog_type=boog_r),
        speld_klas(
            volgorde=4,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1300",
            boog_type=boog_r),

        # WA zilveren ster, Compound
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1000",
            boog_type=boog_c),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1100",
            boog_type=boog_c),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_WA_STER_ZILVER,
            beschrijving="1200",
            boog_type=boog_c),
        speld_klas(
            volgorde=4,
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
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Groen",
            boog_type=None),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Grijs",
            boog_type=None),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Wit",
            boog_type=None),
        speld_klas(
            volgorde=4,
            categorie=SPELD_CATEGORIE_WA_ARROWHEAD,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=5,
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
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Wit",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Blauw",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Rood",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Goud",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD,
            beschrijving="Purper",
            boog_type=None),

        # WA zilveren target award
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Wit",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Zwart",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Blauw",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Rood",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Goud",
            boog_type=None),
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER,
            beschrijving="Purper",
            boog_type=None),

    ]

    speld_klas.objects.bulk_create(bulk)


def maak_spelden_nl_tussenspelden(apps, _):

    speld_klas = apps.get_model('Spelden', 'Speld')

    bulk = [
        # WA target awards
        speld_klas(
            volgorde=1,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="950",
            boog_type=None),
        speld_klas(
            volgorde=2,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1050",
            boog_type=None),
        speld_klas(
            volgorde=3,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1150",
            boog_type=None),
        speld_klas(
            volgorde=4,
            categorie=SPELD_CATEGORIE_NL_TUSSENSPELD,
            beschrijving="1250",
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
                ('beschrijving', models.CharField(max_length=20)),
                ('categorie', models.CharField(choices=[('Ws', 'WA ster'), ('Wz', 'WA zilveren ster'),
                                                        ('Wt', 'WA Target award'), ('Wa', 'WA arrowhead speld'),
                                                        ('Ng', 'NL graadspeld'), ('Na', 'NL graadspeld algemeen'),
                                                        ('Nt', 'NL tussenspeld')],
                                               max_length=2)),
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
            field=models.CharField(choices=[('Ws', 'WA ster'), ('Wz', 'WA zilveren ster'), ('Wt', 'WA Target award'),
                                            ('Wa', 'WA arrowhead speld'), ('Ng', 'NL graadspeld'),
                                            ('Na', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')],
                                   default='Ws', max_length=2),
        ),
        migrations.CreateModel(
            name='SpeldLimiet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('afstand', models.PositiveSmallIntegerField()),
                ('aantal_doelen', models.PositiveSmallIntegerField()),
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('leeftijdsklasse', models.ForeignKey(on_delete=PROTECT, to='BasisTypen.leeftijdsklasse')),
                ('speld', models.ForeignKey(on_delete=PROTECT, to='Spelden.speld')),
            ],
            options={
                'verbose_name': 'Speld limiet',
                'verbose_name_plural': 'Speld limieten',
            },
        ),
        migrations.RunPython(maak_spelden_wa_ster, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_arrowhead, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_wa_target_awards, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(maak_spelden_nl_tussenspelden, reverse_code=migrations.RunPython.noop),
    ]

    krak

# end of file
