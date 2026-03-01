# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0122_mutatie'),
        ('CompLaagBond', 'm0001_initial'),
        ('CompLaagRayon', 'm0001_initial'),
        ('TijdelijkeCodes', 'm0008_cleanup'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='KampioenschapTeamKlasseLimiet',
        ),
        migrations.DeleteModel(
            name='KampioenschapIndivKlasseLimiet',
        ),
        migrations.DeleteModel(
            name='KampioenschapTeam',
        ),
        migrations.DeleteModel(
            name='KampioenschapSporterBoog',
        ),
        migrations.DeleteModel(
            name='Kampioenschap',
        ),
    ]

# end of file
