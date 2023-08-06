# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0098_titels'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='kampioenschap',
            old_name='nhb_rayon',
            new_name='rayon',
        ),
        migrations.RenameField(
            model_name='regiocompetitie',
            old_name='nhb_regio',
            new_name='regio',
        ),
    ]

# end of file
