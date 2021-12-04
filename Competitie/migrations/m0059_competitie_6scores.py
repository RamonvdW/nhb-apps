# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0058_competitie_datum_fase_j'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='aantal_scores_voor_rk_deelname',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='datum_klassegrenzen_rk_bk_teams',
            new_name='datum_klassengrenzen_rk_bk_teams',
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='klassegrenzen_vastgesteld',
            new_name='klassengrenzen_vastgesteld',
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='klassegrenzen_vastgesteld_rk_bk',
            new_name='klassengrenzen_vastgesteld_rk_bk',
        ),
    ]

# end of file
