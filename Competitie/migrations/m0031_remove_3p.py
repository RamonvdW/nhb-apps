# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0030_voorkeur_teamtype'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='deelcompetitie',
            name='regio_team_punten_model',
            field=models.CharField(choices=[('2P', 'Twee punten systeem (2/1/0)'),
                                            ('SS', 'Cumulatief: som van team totaal elke ronde'),
                                            ('F1', 'Formule 1 systeem (10/8/6/5/4/3/2/1)')], default='2P', max_length=2),
        ),
    ]

# end of file
