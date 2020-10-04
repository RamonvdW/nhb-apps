# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0004_wedstrijduitslag'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijduitslag',
            name='is_bevroren',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
