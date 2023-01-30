# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0086_prep_bk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='result_volgorde',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]

# end of file
