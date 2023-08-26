# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0026_vereniging_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='sporter',
            name='bij_vereniging',
        ),
        migrations.RenameField(
            model_name='sporter',
            old_name='bij_vereniging_new',
            new_name='bij_vereniging',
        ),
    ]

# end of file
