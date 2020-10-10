# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0013_squashed'),
        ('BasisTypen', 'm0010_squashed'),
        ('NhbStructuur', 'm0015_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heeft_interesse', models.BooleanField(default=True)),
                ('voor_wedstrijd', models.BooleanField(default=False)),
                ('account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Account.Account')),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BasisTypen.BoogType')),
                ('nhblid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.NhbLid')),
            ],
            options={
                'verbose_name': 'SchutterBoog',
                'verbose_name_plural': 'SchuttersBoog',
            },
        ),
        migrations.CreateModel(
            name='SchutterVoorkeuren',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voorkeur_dutchtarget_18m', models.BooleanField(default=False)),
                ('voorkeur_meedoen_competitie', models.BooleanField(default=True)),
                ('account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Account.Account')),
                ('nhblid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.NhbLid')),
            ],
            options={
                'verbose_name': 'Schutter voorkeuren',
                'verbose_name_plural': 'Schutter voorkeuren',
            },
        ),
    ]

# end of file
