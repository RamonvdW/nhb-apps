# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('TijdelijkeCodes', 'm0002_registreer'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='tijdelijkecode',
            old_name='hoortbij_account',
            new_name='hoort_bij_account',
        ),
        migrations.RenameField(
            model_name='tijdelijkecode',
            old_name='hoortbij_functie',
            new_name='hoort_bij_functie',
        ),
        migrations.RenameField(
            model_name='tijdelijkecode',
            old_name='hoortbij_gast',
            new_name='hoort_bij_gast_reg',
        ),
        migrations.RenameField(
            model_name='tijdelijkecode',
            old_name='hoortbij_kampioenschap',
            new_name='hoort_bij_kampioen',
        ),
    ]

# end of file
