# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0017_kampioenschapschutterboog'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='DeelcompetitieKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.CompetitieKlasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie Klasse Limiet',
                'verbose_name_plural': 'Deelcompetitie Klasse Limieten',
            },
        ),
    ]

# end of file
