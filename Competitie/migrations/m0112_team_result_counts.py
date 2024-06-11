# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0111_logboekjes'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='result_counts',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

# end of file
