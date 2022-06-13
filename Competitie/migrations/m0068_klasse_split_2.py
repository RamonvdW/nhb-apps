# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0067_klasse_split_1'),
    ]

    # migratie functies
    operations = [
        # gebruik van CompetitieKlasse migreren naar de nieuwe klassen
        migrations.AddField(
            model_name='competitiemutatie',
            name='indiv_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieindivklasse'),
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='team_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieteamklasse'),
        ),
        migrations.AddField(
            model_name='deelcompetitieklasselimiet',
            name='indiv_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieindivklasse'),
        ),
        migrations.AddField(
            model_name='deelcompetitieklasselimiet',
            name='team_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieteamklasse'),
        ),
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='indiv_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieindivklasse'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='team_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieteamklasse'),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='indiv_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieindivklasse'),
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='team_klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.competitieteamklasse'),
        ),
    ]

# end of file
