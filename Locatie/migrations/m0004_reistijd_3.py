# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Locatie', 'm0003_reistijd_2'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='reistijd',
            name='vanaf_postcode',
        ),
    ]

# end of file
