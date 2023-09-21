# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Wedstrijden.definities import AANTAL_SCHEIDS_GEEN_KEUZE


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0046_kwalificatiescores'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='aantal_scheids',
            field=models.PositiveSmallIntegerField(default=AANTAL_SCHEIDS_GEEN_KEUZE),
        ),
    ]

# end of file
