# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Competitie', 'm0119_squashed'),
        ('Functie', 'm0028_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Taak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_afgerond', models.BooleanField(default=False)),
                ('deadline', models.DateField()),
                ('beschrijving', models.TextField(max_length=5000)),
                ('log', models.TextField(blank=True, max_length=5000)),
                ('aangemaakt_door', models.ForeignKey(blank=True, null=True,
                                                      on_delete=models.deletion.SET_NULL,
                                                      related_name='account_taken_aangemaakt', to='Account.account')),
                ('toegekend_aan_functie', models.ForeignKey(blank=True, null=True,
                                                            on_delete=models.deletion.SET_NULL,
                                                            related_name='functie_taken', to='Functie.functie')),
                ('onderwerp', models.CharField(default='', max_length=100)),
            ],
            options={
                'verbose_name': 'Taak',
                'verbose_name_plural': 'Taken',
            },
        ),
    ]

# end of file
