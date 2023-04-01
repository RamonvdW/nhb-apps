# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0091_indiv_teams_split'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='kampioenschapindivklasselimiet',
            name='indiv_klasse',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieindivklasse'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='kampioenschapteamklasselimiet',
            name='team_klasse',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieteamklasse'),
            preserve_default=False,
        ),
    ]

# end of file
