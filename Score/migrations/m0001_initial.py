# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Schutter', 'm0001_initial'),
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
            ],
        ),
        migrations.CreateModel(
            name='ScoreHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_waarde', models.PositiveSmallIntegerField()),
                ('nieuwe_waarde', models.PositiveSmallIntegerField()),
                ('datum', models.DateField()),
                ('notitie', models.CharField(max_length=100)),
                ('door_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Score.Score')),
            ],
        ),
    ]
