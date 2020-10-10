# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import datetime
import django.db.models.deletion
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0013_squashed'),
        ('Schutter', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waarde', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Schutter.SchutterBoog')),
                ('is_ag', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ScoreHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_waarde', models.PositiveSmallIntegerField()),
                ('nieuwe_waarde', models.PositiveSmallIntegerField()),
                ('notitie', models.CharField(max_length=100)),
                ('door_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Account.Account')),
                ('score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Score.Score')),
                ('when', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

# end of file
