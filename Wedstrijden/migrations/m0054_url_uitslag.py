# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0053_verstop'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='url_uitslag',
            field=models.CharField(default='', max_length=128),
        ),
    ]

# end of file
