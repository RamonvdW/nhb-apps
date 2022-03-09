# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0021_nieuwe_uitslag'),
        ('Competitie', 'm0071_matches'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='competitiewedstrijdenplan',
            name='wedstrijden',
        ),
        migrations.RemoveField(
            model_name='competitiewedstrijduitslag',
            name='nieuwe_uitslag',
        ),
        migrations.RemoveField(
            model_name='competitiewedstrijduitslag',
            name='scores',
        ),
        migrations.DeleteModel(
            name='CompetitieWedstrijd',
        ),
        migrations.DeleteModel(
            name='CompetitieWedstrijdenPlan',
        ),
        migrations.DeleteModel(
            name='CompetitieWedstrijdUitslag',
        ),
    ]

# end of file
