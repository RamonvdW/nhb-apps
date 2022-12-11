# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0032_niet_tonen'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijdkorting',
            name='voor_vereniging',
        ),
    ]

# end of file
