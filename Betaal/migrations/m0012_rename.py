# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0011_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='betaalinstellingenvereniging',
            old_name='akkoord_via_nhb',
            new_name='akkoord_via_bond',
        ),
    ]

# end of file
