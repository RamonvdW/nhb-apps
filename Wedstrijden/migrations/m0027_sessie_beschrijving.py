# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0026_migratie_3'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdsessie',
            name='beschrijving',
            field=models.CharField(default='', max_length=50),
        ),
    ]

# end of file
