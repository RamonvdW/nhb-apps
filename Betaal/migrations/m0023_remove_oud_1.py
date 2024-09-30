# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0022_optional'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='betaaltransactie',
            name='bedrag_euro_boeking',
        ),
    ]

# end of file
