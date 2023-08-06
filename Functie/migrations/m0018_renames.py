# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0017_squashed'),
        ('Registreer', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='functie',
            old_name='nhb_rayon',
            new_name='rayon',
        ),
        migrations.RenameField(
            model_name='functie',
            old_name='nhb_regio',
            new_name='regio',
        ),
        migrations.RenameField(
            model_name='functie',
            old_name='nhb_ver',
            new_name='vereniging',
        ),
    ]

# end of file
