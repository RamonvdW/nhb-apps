# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0007_squashed'),
        ('Locatie', 'm0007_rename'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='EvenementLocatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('zichtbaar', models.BooleanField(default=True)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('plaats', models.CharField(blank=True, default='', max_length=50)),
                ('adres_lat', models.CharField(blank=True, default='', max_length=10)),
                ('adres_lon', models.CharField(blank=True, default='', max_length=10)),
                ('notities', models.TextField(blank=True, max_length=1024)),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Evenement locatie',
            },
        ),
    ]

# end of file
