# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0005_bestelmutatie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelmutatie',
            name='bestelling',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelling'),
        ),
        migrations.AddField(
            model_name='bestelmutatie',
            name='betaling_is_gelukt',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file