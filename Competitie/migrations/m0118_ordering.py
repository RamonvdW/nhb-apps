# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0117_mutatie_door_langer'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='competitie',
            options={'ordering': ['begin_jaar', 'afstand'],
                     'verbose_name': 'Competitie', 'verbose_name_plural': 'Competities'},
        ),
        migrations.AlterModelOptions(
            name='kampioenschap',
            options={'ordering': ['competitie__afstand', 'deel', 'rayon__rayon_nr'],
                     'verbose_name': 'Kampioenschap', 'verbose_name_plural': 'Kampioenschappen'},
        ),
    ]

# end of file
