# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0037_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijdlocatie',
            name='max_dt_per_baan',
        ),
    ]

# end of file
