# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0031_squashed'),
        ('Functie', 'm0016_rol_mww'),
        ('Competitie', 'm0089_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveIndex(
            model_name='regiocompetitiesporterboog',
            name='Competitie__aantal__abf0e4_idx',
        ),
        migrations.RenameModel(
            old_name='DeelKampioenschap',
            new_name='Kampioenschap',
        ),
        migrations.RenameModel(
            old_name='DeelCompetitie',
            new_name='Regiocompetitie',
        ),
        migrations.RenameModel(
            old_name='DeelcompetitieRonde',
            new_name='RegiocompetitieRonde',
        ),
        migrations.RenameField(
            model_name='competitiemutatie',
            old_name='deelcompetitie',
            new_name='regiocompetitie',
        ),
        migrations.RenameField(
            model_name='regiocompetitieronde',
            old_name='deelcompetitie',
            new_name='regiocompetitie',
        ),
        migrations.RenameField(
            model_name='regiocompetitiesporterboog',
            old_name='deelcompetitie',
            new_name='regiocompetitie',
        ),
        migrations.RenameField(
            model_name='regiocompetitieteam',
            old_name='deelcompetitie',
            new_name='regiocompetitie',
        ),
        migrations.RenameField(
            model_name='regiocompetitieteampoule',
            old_name='deelcompetitie',
            new_name='regiocompetitie',
        ),
        migrations.AddIndex(
            model_name='regiocompetitiesporterboog',
            index=models.Index(fields=['aantal_scores', 'regiocompetitie'], name='Competitie__aantal__258001_idx'),
        ),
        migrations.AlterModelOptions(
            name='kampioenschap',
            options={'verbose_name': 'Kampioenschap', 'verbose_name_plural': 'Kampioenschappen'},
        ),
        migrations.AlterModelOptions(
            name='competitiematch',
            options={'verbose_name': 'Competitie match', 'verbose_name_plural': 'Competitie matches'},
        ),
    ]

# end of file
