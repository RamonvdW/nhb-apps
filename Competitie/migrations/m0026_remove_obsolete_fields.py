# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0025_klassegrenzen_vastgesteld'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kampioenschapschutterboog',
            name='deelname_bevestigd',
        ),
        migrations.RemoveField(
            model_name='kampioenschapschutterboog',
            name='is_afgemeld',
        ),
    ]

# end of file
