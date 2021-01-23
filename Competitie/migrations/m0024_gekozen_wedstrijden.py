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
        ('Wedstrijden', 'm0006_squashed'),
        ('Competitie', 'm0023_protect_schutterboog_delete'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_gekozen_wedstrijden',
            field=models.ManyToManyField(blank=True, to='Wedstrijden.Wedstrijd'),
        ),
    ]

# end of file
