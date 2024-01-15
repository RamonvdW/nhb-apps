# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0025_herinnering'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_btw_nr',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
    ]

# end of file
