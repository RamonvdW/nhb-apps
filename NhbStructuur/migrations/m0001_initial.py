# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion
import NhbStructuur.models


class Migration(migrations.Migration):

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='NhbRayon',
            fields=[
                ('rayon_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
                ('geografisch_gebied', models.CharField(max_length=50)),
            ],
            options={'verbose_name': 'Nhb rayon', 'verbose_name_plural': 'Nhb rayons'},
        ),
        migrations.CreateModel(
            name='NhbRegio',
            fields=[
                ('regio_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
                ('rayon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRayon')),
            ],
            options={'verbose_name': 'Nhb regio', 'verbose_name_plural': 'Nhb regios'},
        ),
        migrations.CreateModel(
            name='NhbLid',
            fields=[
                ('nhb_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('voornaam', models.CharField(max_length=100)),
                ('achternaam', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=150)),
                ('geboorte_datum', models.DateField(validators=[NhbStructuur.models.validate_geboorte_datum])),
                ('postcode', models.CharField(max_length=10)),
                ('huisnummer', models.CharField(max_length=10)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('is_rolstoelschutter', models.BooleanField(default=False)),
                ('is_actief_lid', models.BooleanField(default=True)),
                ('sinds_datum', models.DateField(validators=[NhbStructuur.models.validate_sinds_datum])),
            ],
            options={'verbose_name': 'Nhb lid', 'verbose_name_plural': 'Nhb leden'},
        ),
        migrations.CreateModel(
            name='NhbVereniging',
            fields=[
                ('nhb_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=200)),
                ('regio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
                ('secretaris_lid',
                 models.ForeignKey(blank=True, null=True,
                                   on_delete=django.db.models.deletion.PROTECT,
                                   to='NhbStructuur.NhbLid')),
            ],
            options={'verbose_name': 'Nhb vereniging', 'verbose_name_plural': 'Nhb verenigingen'},
        ),
        # losse AddField ivm circulaire dependency
        migrations.AddField(
            model_name='nhblid',
            name='bij_vereniging',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    to='NhbStructuur.NhbVereniging'),
        ),
    ]

# end of file

