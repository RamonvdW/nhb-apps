# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0102_vereniging_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='regiocompetitiesporterboog',
            name='bij_vereniging',
        ),
        migrations.RenameField(
            model_name='regiocompetitiesporterboog',
            old_name='bij_vereniging_new',
            new_name='bij_vereniging',
        ),
        migrations.AlterField(
            model_name='regiocompetitiesporterboog',
            name='bij_vereniging',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),

        migrations.RemoveField(
            model_name='regiocompetitieteam',
            name='vereniging',
        ),
        migrations.RenameField(
            model_name='regiocompetitieteam',
            old_name='vereniging_new',
            new_name='vereniging',
        ),
        migrations.AlterField(
            model_name='regiocompetitieteam',
            name='vereniging',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),

        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='bij_vereniging',
        ),
        migrations.RenameField(
            model_name='kampioenschapsporterboog',
            old_name='bij_vereniging_new',
            new_name='bij_vereniging',
        ),

        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='vereniging',
        ),
        migrations.RenameField(
            model_name='kampioenschapteam',
            old_name='vereniging_new',
            new_name='vereniging',
        ),

        migrations.RemoveField(
            model_name='competitiematch',
            name='vereniging',
        ),
        migrations.RenameField(
            model_name='competitiematch',
            old_name='vereniging_new',
            new_name='vereniging',
        ),
    ]

# end of file
