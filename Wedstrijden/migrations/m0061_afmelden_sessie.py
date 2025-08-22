# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # migratie functies
    dependencies = [
        ('Wedstrijden', 'm0060_bestelling'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijdinschrijving',
            name='sessie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                    to='Wedstrijden.wedstrijdsessie'),
        ),
    ]

# end of file
