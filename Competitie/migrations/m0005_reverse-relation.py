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
        ('Competitie', 'm0004_functie'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='competitie',
            name='klassen_indiv',
        ),
        migrations.RemoveField(
            model_name='competitie',
            name='klassen_team',
        ),
        migrations.AddField(
            model_name='competitiewedstrijdklasse',
            name='competitie',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.Competitie'),
        ),
        migrations.AddField(
            model_name='competitiewedstrijdklasse',
            name='is_team',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='deelcompetitie',
            name='competitie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.Competitie'),
        ),
    ]

# end of file
