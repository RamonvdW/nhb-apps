# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField(null=True)),
                ('site_versie', models.CharField(max_length=20)),
                ('gebruiker', models.CharField(max_length=50)),
                ('in_rol', models.CharField(blank=True, default='?', max_length=100)),
                ('op_pagina', models.CharField(max_length=50)),
                ('volledige_url', models.CharField(blank=True, max_length=250, null=True)),
                ('bevinding', models.CharField(choices=[('8', 'Tevreden'), ('6', 'Bruikbaar'), ('4', 'Moet beter')], max_length=1)),
                ('is_afgehandeld', models.BooleanField(default=False)),
                ('feedback', models.TextField()),
            ],
            options={
                'verbose_name': 'Feedback',
                'verbose_name_plural': 'Feedback',
            },
        ),
    ]

# end of file
