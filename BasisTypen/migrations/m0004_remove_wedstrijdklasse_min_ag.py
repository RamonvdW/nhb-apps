# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0003_min_wedstrijdleeftijd'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijdklasse',
            name='min_ag',
        ),
    ]

# end of file
