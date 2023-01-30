# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0019_erelid'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='sportervoorkeuren',
            old_name='para_met_rolstoel',
            new_name='para_voorwerpen',
        ),
    ]

# end of file
