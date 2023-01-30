# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0085_result_volgorde'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='kampioenschapsporterboog',
            old_name='regio_scores',
            new_name='gemiddelde_scores',
        ),
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='result_bk_teamscore_1',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='result_bk_teamscore_2',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]

# end of file
