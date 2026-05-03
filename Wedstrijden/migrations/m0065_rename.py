# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0064_afgemeld'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='wedstrijdafgemeld',
            old_name='bestelling',
            new_name='bestelling_regel',
        ),
        migrations.RenameField(
            model_name='wedstrijdinschrijving',
            old_name='bestelling',
            new_name='bestelling_regel',
        ),
    ]

# end of file
