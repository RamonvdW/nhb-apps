# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0017_kampioenschapschutterboog'),
        ('Overig', 'm0004_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sitetijdelijkeurl',
            name='hoortbij_kampioenschap',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.KampioenschapSchutterBoog'),
        ),
    ]

# end of file
