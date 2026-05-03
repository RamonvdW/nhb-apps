# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0008_admin'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='evenementafgemeld',
            old_name='bestelling',
            new_name='bestelling_regel',
        ),
        migrations.RenameField(
            model_name='evenementinschrijving',
            old_name='bestelling',
            new_name='bestelling_regel',
        ),
    ]

# end of file
