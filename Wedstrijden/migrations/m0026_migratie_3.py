# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0025_migratie_2'),
        ('Bestel', 'm0011_migratie_1')
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijd',
            name='oud',
        ),
        migrations.RemoveField(
            model_name='wedstrijdinschrijving',
            name='oud',
        ),
        migrations.RemoveField(
            model_name='wedstrijdkortingscode',
            name='oud',
        ),
        migrations.RemoveField(
            model_name='wedstrijdsessie',
            name='oud',
        ),
    ]

# end of file
