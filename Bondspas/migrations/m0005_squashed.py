# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Bondspas', 'm0003_squashed'),
                ('Bondspas', 'm0004_delete')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
    ]

# end of file
