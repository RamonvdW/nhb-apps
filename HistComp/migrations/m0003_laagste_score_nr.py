# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0002_boogtype_optional'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='histcompetitieindividueel',
            name='laagste_score_nr',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

# end of file
