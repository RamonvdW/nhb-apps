# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0039_renames_6'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_dagdeel',
            field=models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"),
                                            ('MA', 'Maandag'), ('DI', 'Dinsdag'), ('WO', 'Woensdag'),
                                            ('DO', 'Donderdag'), ('VR', 'Vrijdag'),
                                            ('ZAT', 'Zaterdag'), ('ZAo', 'Zaterdagochtend'), ('ZAm', 'Zaterdagmiddag'),
                                            ('ZON', 'Zondag'), ('ZOo', 'Zondagochtend'), ('ZOm', 'Zondagmiddag'), ('WE', 'Weekend')], default='GN', max_length=3),
        ),
    ]

# end of file
