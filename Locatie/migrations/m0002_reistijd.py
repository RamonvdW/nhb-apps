# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Locatie', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Reistijd',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vanaf_postcode', models.CharField(default='', max_length=6)),
                ('vanaf_lat', models.CharField(default='', max_length=10)),
                ('vanaf_lon', models.CharField(default='', max_length=10)),
                ('naar_postcode', models.CharField(default='', max_length=6)),
                ('naar_lat', models.CharField(default='', max_length=10)),
                ('naar_lon', models.CharField(default='', max_length=10)),
                ('reistijd_min', models.PositiveSmallIntegerField(default=0)),
                ('op_datum', models.DateField(default='2000-01-01')),
            ],
            options={
                'verbose_name': 'Reistijd',
                'verbose_name_plural': 'Reistijden',
            },
        ),
        migrations.AddField(
            model_name='locatie',
            name='adres_lat',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AddField(
            model_name='locatie',
            name='adres_lon',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AddField(
            model_name='locatie',
            name='postcode',
            field=models.CharField(default='', max_length=6),
        ),
    ]

# end of file
