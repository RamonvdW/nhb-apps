# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0008_deelcompetitieronde'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_notitie',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_dagdeel',
            field=models.CharField(choices=[('GN', 'Geen voorkeur'),
                                            ('AV', "'s Avonds"),
                                            ('ZA', 'Zaterdag'),
                                            ('ZO', 'Zondag'),
                                            ('WE', 'Weekend')],
                                   default='GN', max_length=2),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_team',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
