# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0045_remove_import'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='deelcompetitie',
            name='toegestane_dagdelen',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
        migrations.AlterField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_dagdeel',
            field=models.CharField(
                choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"), ('MA', 'Maandag'), ('MAa', 'Maandagavond'),
                         ('DI', 'Dinsdag'), ('DIa', 'Dinsdagavond'), ('WO', 'Woensdag'), ('WOa', 'Woensdagavond'),
                         ('DO', 'Donderdag'), ('DOa', 'Donderdagavond'), ('VR', 'Vrijdag'), ('VRa', 'Vrijdagavond'),
                         ('ZAT', 'Zaterdag'), ('ZAo', 'Zaterdagochtend'), ('ZAm', 'Zaterdagmiddag'),
                         ('ZAa', 'Zaterdagavond'), ('ZON', 'Zondag'), ('ZOo', 'Zondagochtend'), ('ZOm', 'Zondagmiddag'),
                         ('ZOa', 'Zondagavond'), ('WE', 'Weekend')], default='GN', max_length=3),
        ),
    ]

# end of file
