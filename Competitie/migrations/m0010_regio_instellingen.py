# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0009_inschrijf_voorkeuren'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='deelcompetitie',
            name='inschrijf_methode',
            field=models.CharField(choices=[('1', 'Kies wedstrijden'),
                                            ('2', 'Naar locatie wedstrijdklasse'),
                                            ('3', 'Voorkeur dagdelen')], default='2', max_length=1),
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='toegestane_dagdelen',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

# end of file
