# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Locatie', 'm0002_reistijd'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='reistijd',
            name='naar_postcode',
        ),
        migrations.RemoveField(
            model_name='locatie',
            name='postcode',
        ),
    ]

# end of file