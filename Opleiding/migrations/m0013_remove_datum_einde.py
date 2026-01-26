# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0012_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='opleidingdiploma',
            name='datum_einde',
        ),
    ]

# end of file
