# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0114_logboekje'),
        ('Locatie', 'm0006_squashed'),
        ('Opleidingen', 'm0006_correcties'),
        ('Vereniging', 'm0007_squashed'),
        ('Wedstrijden', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RenameModel(
            old_name='Locatie',
            new_name='WedstrijdLocatie',
        ),
        migrations.AlterModelOptions(
            name='wedstrijdlocatie',
            options={'verbose_name': 'Wedstrijd locatie'},
        ),
    ]

# end of file
