# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('CompLaagRayon', 'm0001_initial'),
        ('Competitie', 'm0123_kamp_migratie'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='cutrk',
            options={'verbose_name': 'Cut RK indiv', 'verbose_name_plural': 'Cuts RK indiv'},
        ),
        migrations.CreateModel(
            name='CutTeamRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=8)),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRayon.kamprk')),
                ('team_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
            options={
                'verbose_name': 'Cut RK teams',
                'verbose_name_plural': 'Cuts RK teams',
            },
        ),
    ]

# end of file
