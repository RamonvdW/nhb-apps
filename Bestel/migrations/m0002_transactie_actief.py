# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0002_minor_changes'),
        ('Bestel', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='actief_mutatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalmutatie'),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='actief_transactie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalactief'),
        ),
    ]

# end of file
