# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0006_betaalactief_meer'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='betaaltransactie',
            old_name='bedrag_euro',
            new_name='bedrag_euro_boeking',
        ),
        migrations.AddField(
            model_name='betaaltransactie',
            name='bedrag_euro_klant',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=7),
        ),
        migrations.RemoveField(
            model_name='betaaltransactie',
            name='klant_bic',
        ),
        migrations.RenameField(
            model_name='betaaltransactie',
            old_name='klant_iban',
            new_name='klant_account',
        ),
        migrations.AlterField(
            model_name='betaaltransactie',
            name='klant_account',
            field=models.CharField(max_length=100),
        ),
    ]

# end of file
