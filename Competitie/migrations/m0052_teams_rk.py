# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0021_is_aspirant__blazoenen'),
        ('Competitie', 'm0051_teamscore_feitelijk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='team_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.teamtype'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse'),
        ),
    ]

# end of file
