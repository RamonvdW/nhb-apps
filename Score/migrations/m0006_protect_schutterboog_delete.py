# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0006_squashed'),
        ('Score', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='score',
            name='schutterboog',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Schutter.SchutterBoog'),
        ),
    ]

# end of file
