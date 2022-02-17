# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0063_afgelast'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='regiocompetitieteam',
            options={'ordering': ['vereniging__ver_nr', 'volg_nr']},
        ),
    ]

# end of file
