# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0008_korting_ver_nr'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='bestelling',
            name='verzendkosten_euro',
        ),
    ]

# end of file
