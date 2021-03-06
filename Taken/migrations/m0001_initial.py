# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Competitie', 'm0013_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Taak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_afgerond', models.BooleanField(default=False)),
                ('deadline', models.DateField()),
                ('beschrijving', models.TextField(max_length=1000)),
                ('handleiding_pagina', models.CharField(max_length=75, blank=True)),
                ('log', models.TextField(max_length=50000, blank=True)),
                ('aangemaakt_door', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='account_taken_aangemaakt', to=settings.AUTH_USER_MODEL)),
                ('deelcompetitie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('toegekend_aan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='account_taken_toegekend', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Taak',
                'verbose_name_plural': 'Taken',
            },
        ),
    ]

# end of file
