# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0007_bestelling_status_admin'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='bestelling',
            old_name='actief_transactie',
            new_name='betaal_actief',
        ),
        migrations.RenameField(
            model_name='bestelling',
            old_name='actief_mutatie',
            new_name='betaal_mutatie',
        ),
    ]

# end of file
