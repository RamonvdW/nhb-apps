# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0011_korting'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='kalenderwedstrijdkortingscode',
            old_name='voor_wedstrijd',
            new_name='voor_wedstrijden',
        ),
    ]

# end of file
