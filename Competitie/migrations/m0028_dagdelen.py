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
        ('Competitie', 'm0027_teams'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_dagdeel',
            field=models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"), ('MA', 'Maandag'), ('DO', 'Dinsdag'), ('WO', 'Woensdag'), ('DO', 'Donderdag'), ('VR', 'Vrijdag'), ('ZA', 'Zaterdag'), ('ZO', 'Zondag'), ('WE', 'Weekend')], default='GN', max_length=2),
        ),
    ]

# end of file
