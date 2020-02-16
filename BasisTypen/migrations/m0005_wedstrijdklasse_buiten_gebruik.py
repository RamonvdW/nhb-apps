# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0004_remove_wedstrijdklasse_min_ag'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdklasse',
            name='buiten_gebruik',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
